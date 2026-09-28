from structure.node import Node
from structure.socket import Socket

class SubtractNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input sockets
        input_socket_a = Socket(name="ValueA", socket_type="FLOAT", direction="INPUT", parent_node=self)
        input_socket_b = Socket(name="ValueB", socket_type="FLOAT", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket_a)
        self.inputs.append(input_socket_b)

        # Define the output socket
        output_socket = Socket(name="OutputValue", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 2, "SubtractNode expects exactly two input variables."
        a, b = input_vars
        return [], [f"({a} - {b})"]
