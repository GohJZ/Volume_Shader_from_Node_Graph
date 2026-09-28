from structure.node import Node
from structure.socket import Socket

class PositionNode(Node):

    def __init__(self):
        super().__init__()

        # Define the output socket
        output_socket = Socket(name="Position", socket_type="VEC3", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        return [], ["p"]
