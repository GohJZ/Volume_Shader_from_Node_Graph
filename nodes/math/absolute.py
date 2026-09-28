from structure.node import Node
from structure.socket import Socket

class AbsoluteNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input socket
        input_socket = Socket(name="Value", socket_type="FLOAT", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket)

        # Define the output socket
        output_socket = Socket(name="OutputValue", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 1, "AbsoluteNode expects exactly one input variable."
        input_var = input_vars[0]
        return [], [f"abs({input_var})"]