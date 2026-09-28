from re import S
from structure.node import Node
from structure.socket import Socket

class ConstantRotationNode(Node):

    def __init__(self, value=(0.0, 0.0, 0.0)):
        super().__init__({"value": value})
        self.is_constant = True

        # Define the output socket
        output_socket = Socket(name="Value", socket_type="ROTATION", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        x, y, z = self.parameters['value']
        return [], [f"vec3({x:.6f}, {y:.6f}, {z:.6f})"]