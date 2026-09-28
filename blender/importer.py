from collections import deque
from structure import *
from nodes import *
from .exceptions import UnsupportedBlenderNodeError

class BlenderImporter:
    """
    A class that translates a Blender node graph representation into the internal node graph structure.
    """
    IGNORED_NODE_TYPES = {
        "GeometryNodeVolumeCube",
        "GeometryNodeVolumeToMesh"
        }

    BLENDER_TO_IR_TYPES = {
        "VALUE": "FLOAT",
        "VECTOR": "VEC3",
        "ROTATION": "ROTATION"
    }

    SUPPORTED_TYPES = set(BLENDER_TO_IR_TYPES)

    def __init__(self):
        self.node_importers = {
                # Constants
                "FunctionNodeInputVector": self.import_constant_vector,
                "FunctionNodeInputFloat": self.import_constant_float,

                # Inputs
                "GeometryNodeInputPosition" : self.import_position,
                "NodeGroupInput": self.import_group_input,
                "NodeGroupOutput": self.import_group_output,

                # Scaler Math Operations
                "ShaderNodeMath": self.import_math,

                # Vector Math Operations
                "ShaderNodeVectorMath": self.import_vector_math,

                # Function Nodes
                "FunctionNodeRotateVector": self.import_rotate_vector,

                # Utility
                "ShaderNodeSeparateXYZ": self.import_separate_xyz,
                "ShaderNodeCombineXYZ": self.import_combine_xyz,
                "ShaderNodeClamp": self.import_clamp
            }

    def import_graph(self, node_tree, context, parent_inputs=None):
        """
        Imports a Blender node graph into the internal representation.

        Steps:
            1. Find blender node tree.
            2. Create IR nodes for each Blender node.
            3. Connect IR nodes based on Blender node connections.
            4. Return the constructed IR graph.
        """
        # Save the old context values for restoration later
        old_parent_inputs = context.parent_inputs
        old_group_outputs = context.group_outputs

        context.parent_inputs = parent_inputs or {}
        context.group_outputs = {}

        # Step 1: Find Blender node tree
        blender_nodes = self.topological_nodes(node_tree)
        blender_links = node_tree.links
        
        # Step 2: Create IR nodes for each Blender node
        for blender_node in blender_nodes:
            ir_node = self.create_ir_node(blender_node, context)

        # Step 3: Connect IR nodes based on Blender node connections
        # Skip links that are handled by the node group input/output nodes
        for link in blender_links:
            if link.to_node.bl_idname == "NodeGroupOutput":
                continue

            if link.to_node.bl_idname == "GeometryNodeGroup":
                continue

            ir_from = context.socket_map.get(link.from_socket)
            ir_to = context.socket_map.get(link.to_socket)

            if ir_from is None or ir_to is None:
                continue

            context.graph.connect(ir_from, ir_to)
        
        outputs = context.group_outputs
        context.parent_inputs = old_parent_inputs
        context.group_outputs = old_group_outputs

        return outputs

    def create_ir_node(self, blender_node, context):

        # Avoid importing nodes that are not relevant to the internal representation
        if blender_node.bl_idname in self.IGNORED_NODE_TYPES:
            return None

        # Handle node groups by recursively importing their internal node trees
        if blender_node.bl_idname == "GeometryNodeGroup":
            if blender_node.node_tree is None:
                return None

            # Create a mapping of parent inputs for the node group
            parent_inputs = {}

            for input_socket in blender_node.inputs:
                if input_socket.is_linked:
                    from_socket = input_socket.links[0].from_socket
                    parent_inputs[input_socket.name] = context.socket_map[from_socket]

                else:
                    socket_type = self.BLENDER_TO_IR_TYPES.get(input_socket.type)

                    if socket_type is None:
                        continue  # Skip unsupported socket types

                    # If the input socket is not linked, create a constant node for its default value
                    parent_inputs[input_socket.name] = self._create_constant_nodes(context, input_socket.default_value, socket_type)

            # Recursively import the internal node tree of the node group
            child_outputs = self.import_graph(blender_node.node_tree, context, parent_inputs)
            
            # Map the outputs of the node group to the outputs of the internal node tree
            for output_socket in blender_node.outputs:
                if output_socket.name in child_outputs:
                    ir_socket = child_outputs[output_socket.name]
                    context.socket_map[output_socket] = ir_socket
                    context.named_outputs[output_socket.name] = ir_socket
            
            return None

        # For other node types, skip directly to this step to create the IR node
        importer = self.node_importers.get(blender_node.bl_idname)

        if importer is None:
            raise UnsupportedBlenderNodeError(blender_node)
        
        return importer(blender_node, context) # Call importer function from node_importers dictionary

    def get_dependencies(self, blender_node, node_tree):
        dependencies = set()

        for link in node_tree.links:
            if link.to_node == blender_node:
                dependencies.add(link.from_node)

        return dependencies

    def get_dependents(self, blender_node, node_tree):
        dependents = set()

        for link in node_tree.links:
            if link.from_node == blender_node:
                dependents.add(link.to_node)

        return dependents

    def topological_nodes(self, node_tree):

        nodes = list(node_tree.nodes)

        in_degree = {node: len(self.get_dependencies(node, node_tree)) for node in nodes}

        queue = deque(node for node in nodes if in_degree[node] == 0)
        sorted_nodes = []

        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)

            for dependent in self.get_dependents(node, node_tree):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_nodes) != len(nodes):
            raise ValueError("Blender node tree has a cycle.")

        return sorted_nodes

    # Importer methods for the entire node tree
    # Caller specifies the output name to be used as the final output of the imported graph.
    def import_node_tree(self, node_tree, output_name=None):

        context = ImportContext()

        self.import_graph(node_tree, context)

        if output_name is not None:
            if output_name not in context.named_outputs:
                raise ValueError(f"Output '{output_name}' not found in the imported node tree.")

        return context

    # Helper methods for creating constant nodes and connecting sockets
    def _create_constant_nodes(self, context, value, socket_type):

        if socket_type == "FLOAT":
            node = ConstantFloatNode(float(value))

        elif socket_type == "VEC3":
            node = ConstantVec3Node(tuple(value))

        elif socket_type == "ROTATION":
            node = ConstantRotationNode(tuple(value))

        else:
            raise NotImplementedError(f"Unsupported constant socket type: {socket_type}")

        context.graph.add_node(node)

        return node.outputs[0]

    # Helper method to connect a Blender socket to an IR input socket, or create a constant node if the Blender socket is not linked
    def _connect_or_default(self, context, blender_socket, ir_input_socket):

        if blender_socket.is_linked:
            from_socket = blender_socket.links[0].from_socket

            ir_output = context.socket_map[from_socket]

            if ir_output.socket_type != ir_input_socket.socket_type:
                ir_output = self._convert_socket(context, ir_output, ir_input_socket.socket_type)

            context.graph.connect(ir_output, ir_input_socket)
            return

        constant = self._create_constant_nodes(context, blender_socket.default_value, ir_input_socket.socket_type)
        context.graph.connect(constant, ir_input_socket)

    def _convert_socket(self, context, output_socket, target_type):

        # Handle conversion from VEC3 to ROTATION
        if output_socket.socket_type == "VEC3" and target_type == "ROTATION":
            conversion = VectorToRotationNode()
            context.graph.add_node(conversion)

            context.graph.connect(output_socket, conversion.inputs[0])

            return conversion.outputs[0]

        raise NotImplementedError(
            f"No conversion from {output_socket.socket_type} "
            f"to {target_type}"
        )



    # Importer methods for specific Blender node types
    # Print input and output socket names to determine use of indeces or names for mapping!

    def import_constant_vector(self, blender_node, context):
        node = ConstantVec3Node(tuple(blender_node.vector))
        context.graph.add_node(node)
        context.socket_map[blender_node.outputs[0]] = node.outputs[0]

        return node

    def import_constant_float(self, blender_node, context):
        node = ConstantFloatNode(blender_node.value)
        context.graph.add_node(node)
        context.socket_map[blender_node.outputs[0]] = node.outputs[0]

        return node

    def import_position(self, blender_node, context):
        position = PositionNode()
        context.graph.add_node(position)
        context.socket_map[blender_node.outputs[0]] = position.outputs[0]

        return position
    
    def import_math(self, blender_node, context):
        operation = blender_node.operation

        if operation == 'ADD':
            node = AddNode()

        elif operation == 'SUBTRACT':
            node = SubtractNode()

        elif operation == 'MULTIPLY':
            node = MultiplyNode()

        elif operation == 'DIVIDE':
            node = DivideNode()

        elif operation == 'MINIMUM':
            node = MinimumNode()

        elif operation == 'MAXIMUM':
            node = MaximumNode()

        elif operation == 'ABSOLUTE':
            node = AbsoluteNode()

        else:
            raise NotImplementedError(f"Math operation '{operation}' is not implemented.")

        context.graph.add_node(node)

        for blender_input, ir_input in zip(blender_node.inputs, node.inputs):
            self._connect_or_default(context, blender_input, ir_input)

        context.socket_map[blender_node.outputs[0]] = node.outputs[0]

        return node

    def import_vector_math(self, blender_node, context):
        operation = blender_node.operation

        if operation == 'ADD':
            node = AddVectorNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
            self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        elif operation == 'SUBTRACT':
            node = SubtractVectorNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
            self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        elif operation == 'SCALE':
            node = MultiplyVectorScalerNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs["Vector"], node.inputs[0])
            self._connect_or_default(context, blender_node.inputs["Scale"], node.inputs[1])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        elif operation == 'DIVIDE':
            node = DivideVectorNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
            self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        elif operation == 'ABSOLUTE':
            node = AbsoluteVectorNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs["Vector"], node.inputs[0])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        elif operation == 'LENGTH':
            node = LengthNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs["Vector"], node.inputs[0])
            context.socket_map[blender_node.outputs["Value"]] = node.outputs[0]

        elif operation == 'MAXIMUM':
            node = MaximumVectorNode()
            context.graph.add_node(node)
            self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
            self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
            context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        else:
            raise NotImplementedError(f"Vector math operation '{operation}' is not implemented.")

        return node

    def import_rotate_vector(self, blender_node, context):
        node = RotateVectorNode()
        context.graph.add_node(node)
        self._connect_or_default(context, blender_node.inputs["Vector"], node.inputs[0])
        self._connect_or_default(context, blender_node.inputs["Rotation"], node.inputs[1])
        context.socket_map[blender_node.outputs["Vector"]] = node.outputs[0]

        return node

    def import_separate_xyz(self, blender_node, context):
        node = SeparateXYZNode()
        context.graph.add_node(node)
        self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
        context.socket_map[blender_node.outputs[0]] = node.outputs[0]
        context.socket_map[blender_node.outputs[1]] = node.outputs[1]
        context.socket_map[blender_node.outputs[2]] = node.outputs[2]

        return node

    def import_combine_xyz(self, blender_node, context):
        node = CombineXYZNode()
        context.graph.add_node(node)
        self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
        self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
        self._connect_or_default(context, blender_node.inputs[2], node.inputs[2])
        context.socket_map[blender_node.outputs[0]] = node.outputs[0]

        return node

    def import_clamp(self, blender_node, context):
        node = ClampNode()
        context.graph.add_node(node)
        self._connect_or_default(context, blender_node.inputs[0], node.inputs[0])
        self._connect_or_default(context, blender_node.inputs[1], node.inputs[1])
        self._connect_or_default(context, blender_node.inputs[2], node.inputs[2])
        context.socket_map[blender_node.outputs[0]] = node.outputs[0]

        return node

    def import_group_input(self, blender_node, context):
        for output in blender_node.outputs:
            if output.name in context.parent_inputs:
                context.socket_map[output] = context.parent_inputs[output.name]

    def import_group_output(self, blender_node, context):
        for input_socket in blender_node.inputs:
            if input_socket.type not in self.SUPPORTED_TYPES: # Skip geometry and other unsupported types
                continue

            if not input_socket.is_linked:
                continue

            from_socket = input_socket.links[0].from_socket
            context.group_outputs[input_socket.name] = context.socket_map[from_socket]
