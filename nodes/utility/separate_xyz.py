from structure.node import Node
from structure.socket import Socket

class SeparateXYZNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input socket
        input_socket = Socket(name="Vector", socket_type="VEC3", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket)

        # Define the output socket
        output_socket_x = Socket(name="X", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        output_socket_y = Socket(name="Y", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        output_socket_z = Socket(name="Z", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket_x)
        self.outputs.append(output_socket_y)
        self.outputs.append(output_socket_z)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 1, "SeparateXYZNode expects exactly one input variables."

        v = input_vars[0]

        expressions = [
            f"{v}.x",
            f"{v}.y",
            f"{v}.z",
        ]

        return [], expressions