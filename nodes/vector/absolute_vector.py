from structure.node import Node
from structure.socket import Socket

class AbsoluteVectorNode(Node):

    def __init__(self):
        super().__init__()

        # Define the input socket
        input_socket = Socket(name="Vector", socket_type="VEC3", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket)

        # Define the output socket
        output_socket = Socket(name="OutputVector", socket_type="VEC3", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 1, "AbsoluteVectorNode expects exactly one input variable."
        input_var = input_vars[0]
        return [], [f"abs({input_var})"]