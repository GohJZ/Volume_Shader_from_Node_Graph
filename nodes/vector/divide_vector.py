from structure.node import Node
from structure.socket import Socket

class DivideVectorNode(Node):
    
    def __init__(self):
        super().__init__()

        # Define the input sockets
        input_socket_a = Socket(name="VectorA", socket_type="VEC3", direction="INPUT", parent_node=self)
        input_socket_b = Socket(name="VectorB", socket_type="VEC3", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket_a)
        self.inputs.append(input_socket_b)

        # Define the output socket
        output_socket = Socket(name="OutputVector", socket_type="VEC3", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 2, "DivideVectorNode expects exactly two input variables."
        a, b = input_vars
        return [], [f"({a} / {b})"]
