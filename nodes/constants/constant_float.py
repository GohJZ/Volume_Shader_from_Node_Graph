from structure.node import Node
from structure.socket import Socket

class ConstantFloatNode(Node):

    def __init__(self, value = 0.0):
        super().__init__({"value": value})
        self.is_constant = True

        # Define the output socket
        output_socket = Socket(name="Value", socket_type="FLOAT", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        return [], [f"{self.parameters['value']:.3f}"]