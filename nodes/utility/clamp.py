from structure.node import Node
from structure.socket import Socket

class ClampNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input sockets
        input_socket_a = Socket(name="Value", socket_type="FLOAT", direction="INPUT", parent_node=self)
        input_socket_b = Socket(name="Min", socket_type="FLOAT", direction="INPUT", parent_node=self)
        input_socket_c = Socket(name="Max", socket_type="FLOAT", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket_a)
        self.inputs.append(input_socket_b)
        self.inputs.append(input_socket_c)

        # Define the output socket
        output_socket = Socket(name="Result", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 3, "ClampNode expects exactly three input variables."
        value, min_val, max_val = input_vars
        return [], [f"clamp({value}, {min_val}, {max_val})"]
