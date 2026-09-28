from structure.node import Node
from structure.socket import Socket

class CombineXYZNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input sockets
        input_socket_x = Socket(name="X", socket_type="FLOAT", direction="INPUT", parent_node=self)
        input_socket_y = Socket(name="Y", socket_type="FLOAT", direction="INPUT", parent_node=self)
        input_socket_z = Socket(name="Z", socket_type="FLOAT", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket_x)
        self.inputs.append(input_socket_y)
        self.inputs.append(input_socket_z)

        # Define the output socket
        output_socket = Socket(name="Vector", socket_type="VEC3", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 3, "CombineXYZNode expects exactly three input variables."

        x, y, z = input_vars

        return [], [f"vec3({x}, {y}, {z})"]