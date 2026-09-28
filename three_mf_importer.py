"""Read implicit 3MF files and map the sphere's calculation into existing IR nodes."""

import argparse
import warnings

import lib3mf

from nodes.constants.constant_float import ConstantFloatNode
from nodes.inputs.position import PositionNode
from nodes.math.subtract import SubtractNode
from nodes.math.add import AddNode
from nodes.math.max import MaximumNode
from nodes.vector.length import LengthNode
from nodes.constants.constant_vec3 import ConstantVec3Node
from nodes.vector.max_vector import MaximumVectorNode
from structure.import_context import ImportContext

from nodes.vector.subtract_vector import SubtractVectorNode
from nodes.vector.absolute_vector import AbsoluteVectorNode
from nodes.math.min import MinimumNode
from nodes.utility.separate_xyz import SeparateXYZNode

from nodes.utility.combine_xyz import CombineXYZNode
from nodes.math.multiply import MultiplyNode


def iter_items(iterator):
    """Let a Lib3MF iterator work in a normal Python for loop."""
    while iterator.MoveNext():
        yield iterator.GetCurrent()


class ThreeMFImporter:
    def __init__(self):
        # Keep the native library and model alive while their objects are used.
        self.wrapper = lib3mf.get_wrapper()
        self.model = None
        # Keep implicit functions by resource ID for function calls.
        self.functions = {}
        # Track function bodies being imported to reject recursive calls.
        self.active_functions = set()

    def read_file(self, path):
        """Return the selected implicit function and its scalar channel name."""
        # Discard function references from the previous file.
        self.functions.clear()
        self.active_functions.clear()

        self.model = self.wrapper.CreateModel()
        reader = self.model.QueryReader("3mf")

        # Lib3MF handles the ZIP package, XML, and resource references.
        reader.SetStrictModeActive(True)  # checks correctness of XML for 2mf
        reader.ReadFromFile(str(path))
        for index in range(reader.GetWarningCount()):
            _, message = reader.GetWarning(index)
            warnings.warn(message, stacklevel=2)

        # Our examples each build one directly referenced level-set object.
        items = list(iter_items(self.model.GetBuildItems()))
        if len(items) != 1:
            raise ValueError("Expected exactly one build item.")
        level_set = items[0].GetObjectResource()
        if not isinstance(level_set, lib3mf.LevelSet):
            raise ValueError("The build object is not a volumetric level set.")

        # The level set chooses the function and the scalar output to display.
        function_id = level_set.GetFunction().GetResourceID()
        channel = level_set.GetChannelName()

        # Collect every implicit function, not just the selected one.
        functions = self.model.GetFunctions()
        while functions.MoveNext():
            candidate = functions.GetCurrentFunction()
            if isinstance(candidate, lib3mf.ImplicitFunction):
                self.functions[candidate.GetResourceID()] = candidate

        # Select the function referenced by the level set.
        function = self.functions.get(function_id)

        if not isinstance(function, lib3mf.ImplicitFunction):
            raise ValueError("The level set does not reference an implicit function.")

        # Check the interface needed later to generate a function of position.
        inputs = {
            port.GetIdentifier(): port for port in iter_items(function.GetInputs())
        }
        outputs = {
            port.GetIdentifier(): port for port in iter_items(function.GetOutputs())
        }
        if (
            "pos" not in inputs
            or inputs["pos"].GetType() != lib3mf.ImplicitPortType.Vector
        ):
            raise ValueError("The function needs a vector input named 'pos'.")
        if (
            channel not in outputs
            or outputs[channel].GetType() != lib3mf.ImplicitPortType.Scalar
        ):
            raise ValueError(f"Scalar output channel {channel!r} was not found.")

        # Reading stays separate from translating these objects into IR nodes.
        return function, channel

    def import_file(self, path):
        """Map the selected scalar field to IR; bounds and transforms come later."""
        function, channel = self.read_file(path)
        if len(list(iter_items(function.GetInputs()))) != 1:
            raise NotImplementedError(
                "Only the position input is supported in this step."
            )

        # Reuse the same context and position node as the Blender importer.
        context = ImportContext()
        position = PositionNode()
        context.graph.add_node(position)
        context.socket_map["inputs.pos"] = position.outputs[0]

        # Names only identify connections. The library's node types select operations.
        nodes = {node.GetIdentifier(): node for node in iter_items(function.GetNodes())}
        reference = function.FindOutput(channel).GetReference()
        context.named_outputs[channel] = self._import_output(
            reference, nodes, context, set()
        )
        return context

    def _resolve_function_call(self, call, nodes):
        """Find the implicit function referenced by a call node."""
        # functionID points to a resource node, not directly to a function.
        port = call.FindInput("functionID")
        if port.GetType() != lib3mf.ImplicitPortType.ResourceID:
            raise ValueError("The functionID input must have type ResourceID.")

        reference = port.GetReference()
        node_id, separator, output_name = reference.partition(".")
        if not separator or node_id not in nodes:
            raise ValueError(f"Unknown function reference: {reference!r}.")

        # Initially, support direct references through ResourceIdNode only.
        resource_node = nodes[node_id]
        if not isinstance(resource_node, lib3mf.ResourceIdNode):
            raise NotImplementedError("functionID must reference a ResourceIdNode.")
        if output_name != "value":
            raise ValueError(f"Unknown resource output: {reference!r}.")

        # Use the resource ID to retrieve the typed function saved by read_file().
        function_id = resource_node.GetResource().GetResourceID()
        function = self.functions.get(function_id)
        if function is None:
            raise NotImplementedError(
                f"Resource {function_id} is not a supported implicit function."
            )

        return function

    def _import_function_call(self, call, output_name, nodes, context, visiting):
        """Expand one called output into the existing IR graph."""
        function = self._resolve_function_call(call, nodes)
        function_id = function.GetResourceID()
        if function_id in self.active_functions:
            raise ValueError("Recursive function calls are not supported.")

        # Match arguments by name, not by their order in the file.
        arguments = {p.GetIdentifier(): p for p in iter_items(call.GetInputs())}
        parameters = {p.GetIdentifier(): p for p in iter_items(function.GetInputs())}
        if set(arguments) != set(parameters) | {"functionID"}:
            raise ValueError("Function call arguments do not match its parameters.")

        outputs = {p.GetIdentifier(): p for p in iter_items(function.GetOutputs())}
        call_outputs = {p.GetIdentifier(): p for p in iter_items(call.GetOutputs())}
        if output_name not in outputs or output_name not in call_outputs:
            raise ValueError(f"Unknown function output: {output_name!r}.")
        output = outputs[output_name]
        if call_outputs[output_name].GetType() != output.GetType():
            raise ValueError(f"Wrong function output type: {output_name!r}.")

        # Each call has its own socket map, but all operations share one graph.
        child = ImportContext()
        child.graph = context.graph
        socket_types = {
            lib3mf.ImplicitPortType.Scalar: "FLOAT",
            lib3mf.ImplicitPortType.Vector: "VEC3",
        }
        if output.GetType() not in socket_types:
            raise NotImplementedError("Only scalar/vector call outputs are supported.")

        for name, parameter in parameters.items():
            expected = socket_types.get(parameter.GetType())
            if expected is None:
                raise NotImplementedError("Only scalar/vector arguments are supported.")
            argument = arguments[name]
            if argument.GetType() != parameter.GetType():
                raise ValueError(f"Wrong argument type: {name!r}.")

            # Evaluate the argument in the caller, then bind it inside the callee.
            socket = self._import_output(
                argument.GetReference(), nodes, context, visiting
            )
            if socket.socket_type != expected:
                raise ValueError(f"Wrong argument socket type: {name!r}.")
            child.socket_map[f"inputs.{name}"] = socket

        child_nodes = {n.GetIdentifier(): n for n in iter_items(function.GetNodes())}

        # Import arguments before entering the function: f(f(p)) is not recursion.
        self.active_functions.add(function_id)
        try:
            result = self._import_output(
                output.GetReference(), child_nodes, child, set()
            )
            if result.socket_type != socket_types[output.GetType()]:
                raise ValueError(f"Wrong result socket type: {output_name!r}.")
            return result
        finally:
            # Also clean up when a called operation is unsupported.
            self.active_functions.remove(function_id)

    def _create_vector_multiply(self, context):
        """Build component-wise multiplication from existing scalar nodes."""
        # Split both vectors so each pair of components can be multiplied.
        a = SeparateXYZNode()
        b = SeparateXYZNode()
        context.graph.add_node(a)
        context.graph.add_node(b)
        result = CombineXYZNode()

        for index in range(3):
            multiply = MultiplyNode()
            context.graph.add_node(multiply)
            context.graph.connect(a.outputs[index], multiply.inputs[0])
            context.graph.connect(b.outputs[index], multiply.inputs[1])
            context.graph.connect(multiply.outputs[0], result.inputs[index])

        # The caller connects A/B to these inputs and adds the result node.
        return result, [a.inputs[0], b.inputs[0]]

    def _import_output(self, reference, nodes, context, visiting):
        """Follow one output's inputs first, then create its IR node."""
        # Reuse an existing socket when several operations share the same result.
        if reference in context.socket_map:
            return context.socket_map[reference]

        node_id, separator, output_name = reference.partition(".")
        if not separator or node_id not in nodes:
            raise ValueError(f"Unknown output reference: {reference!r}.")
        if node_id in visiting:
            raise ValueError(f"Cycle detected at node {node_id!r}.")

        # Only the operations needed by the sphere are added in this step.
        source = nodes[node_id]

        if isinstance(source, lib3mf.FunctionCallNode):
            # Calls expand into ordinary nodes; they have no dedicated GLSL node.
            visiting.add(node_id)
            try:
                result = self._import_function_call(
                    source, output_name, nodes, context, visiting
                )
                context.socket_map[reference] = result
                return result
            finally:
                visiting.remove(node_id)

        # Usually inputs belong to one node; expanded operations override this.
        input_sockets = None

        if isinstance(source, lib3mf.ConstantNode):
            node = ConstantFloatNode(source.GetConstant())
            input_names, result_name = (), "value"

        elif isinstance(source, lib3mf.LengthNode):
            node = LengthNode()
            input_names, result_name = ("A",), "result"
        elif isinstance(source, lib3mf.SubtractionNode):
            # Subtraction can return either a scalar or a vector.
            if source.FindInput("A").GetType() == lib3mf.ImplicitPortType.Vector:
                node = SubtractVectorNode()
            else:
                node = SubtractNode()
            input_names, result_name = ("A", "B"), "result"
        elif isinstance(source, lib3mf.AdditionNode):
            node = AddNode()
            input_names, result_name = ("A", "B"), "result"

        elif isinstance(source, lib3mf.MaxNode):
            # Maximum can operate on scalars or on vectors.
            if source.FindInput("A").GetType() == lib3mf.ImplicitPortType.Vector:
                node = MaximumVectorNode()
            else:
                node = MaximumNode()
            input_names, result_name = ("A", "B"), "result"

        elif isinstance(source, lib3mf.ConstVecNode):
            # Read the source constant into the colleague's vector node.
            node = ConstantVec3Node(tuple(source.GetVector().Coordinates))
            input_names, result_name = (), "vector"

        elif isinstance(source, lib3mf.AbsNode):
            # The box takes the absolute value of each position component.
            node = AbsoluteVectorNode()
            input_names, result_name = ("A",), "result"

        elif isinstance(source, lib3mf.MinNode):
            node = MinimumNode()
            input_names, result_name = ("A", "B"), "result"

        elif isinstance(source, lib3mf.DecomposeVectorNode):
            # This operation has three outputs instead of one.
            node = SeparateXYZNode()
            input_names = ("A",)

        elif isinstance(source, lib3mf.ComposeVectorNode):
            node = CombineXYZNode()
            input_names, result_name = ("x", "y", "z"), "result"

        elif isinstance(source, lib3mf.MultiplicationNode):
            if source.FindInput("A").GetType() == lib3mf.ImplicitPortType.Vector:
                # Expand A * B into three scalar products and one vector result.
                node, input_sockets = self._create_vector_multiply(context)
            else:
                node = MultiplyNode()
            input_names, result_name = ("A", "B"), "result"
        else:
            raise NotImplementedError(
                f"Unsupported operation {type(source).__name__} at node {node_id!r}."
            )

        # Match the source output names to the existing IR socket order.
        output_names = (
            ("x", "y", "z")
            if isinstance(source, lib3mf.DecomposeVectorNode)
            else (result_name,)
        )
        outputs = {
            port.GetIdentifier(): port for port in iter_items(source.GetOutputs())
        }
        if output_name not in output_names or set(outputs) != set(output_names):
            raise ValueError(f"Unknown output reference: {reference!r}.")

        for name, socket in zip(output_names, node.outputs):
            expected_type = (
                lib3mf.ImplicitPortType.Vector
                if socket.socket_type == "VEC3"
                else lib3mf.ImplicitPortType.Scalar
            )
            if outputs[name].GetType() != expected_type:
                raise NotImplementedError(
                    f"Unsupported operation output type at {node_id}.{name}."
                )

        # Match named ports explicitly: subtraction must stay A minus B.
        inputs = {port.GetIdentifier(): port for port in iter_items(source.GetInputs())}
        if set(inputs) != set(input_names):
            raise ValueError(f"Unexpected input ports on node {node_id!r}.")
        visiting.add(node_id)

        # Expanded operations may receive inputs on different internal nodes.
        if input_sockets is None:
            input_sockets = node.inputs
        for name, input_socket in zip(input_names, input_sockets):
            port = inputs[name]
            expected_type = (
                lib3mf.ImplicitPortType.Vector
                if input_socket.socket_type == "VEC3"
                else lib3mf.ImplicitPortType.Scalar
            )
            if port.GetType() != expected_type:
                raise ValueError(f"Wrong input type at {node_id}.{name}.")
            output_socket = self._import_output(
                port.GetReference(), nodes, context, visiting
            )
            context.graph.connect(output_socket, input_socket)
        visiting.remove(node_id)

        # Add dependencies first. The colleague's generator handles GLSL ordering.
        context.graph.add_node(node)
        # Cache every output so X, Y and Z share one imported node.
        for name, socket in zip(output_names, node.outputs):
            context.socket_map[f"{node_id}.{name}"] = socket

        return context.socket_map[reference]


def print_function(function, channel):
    """Print the calculation so its connections can be followed by hand."""
    print(f"Function: {function.GetDisplayName()}")
    print(f"Selected output: {channel}")
    print("Inputs:")
    for port in iter_items(function.GetInputs()):
        print(f"  {port.GetIdentifier()}: {port.GetType().name}")

    # Node identifiers and port references describe the equation, not shape names.
    print("Nodes:")
    for node in iter_items(function.GetNodes()):
        identifier = node.GetIdentifier()
        print(f"  {identifier}: {type(node).__name__}")

        # Constants store values directly rather than receiving them through links.
        if isinstance(node, lib3mf.ConstantNode):
            print(f"    value = {node.GetConstant()}")
        elif isinstance(node, lib3mf.ConstVecNode):
            print(f"    value = {tuple(node.GetVector().Coordinates)}")
        elif isinstance(node, lib3mf.ResourceIdNode):
            print(f"    resource ID = {node.GetResource().GetResourceID()}")

        for port in iter_items(node.GetInputs()):
            print(f"    {port.GetIdentifier()} <- {port.GetReference()}")
        for port in iter_items(node.GetOutputs()):
            print(f"    output: {identifier}.{port.GetIdentifier()}")

    # The selected output reference will become the returned GLSL expression later.
    print("Function outputs:")
    for port in iter_items(function.GetOutputs()):
        print(f"  {port.GetIdentifier()} <- {port.GetReference()}")


if __name__ == "__main__":
    # Run this small inspection step without opening Blender.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to an implicit 3MF file")
    args = parser.parse_args()

    try:
        importer = ThreeMFImporter()
        function, channel = importer.read_file(args.path)
        print_function(function, channel)
    except (OSError, ValueError, lib3mf.ELib3MFException) as error:
        parser.exit(1, f"Error: {error}\n")
