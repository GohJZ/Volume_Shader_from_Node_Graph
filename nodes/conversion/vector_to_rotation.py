from structure.node import Node
from structure.socket import Socket

class VectorToRotationNode(Node):

    def __init__(self):
        super().__init__()

        self.inputs.append(Socket(name="Vector", socket_type="VEC3", direction="INPUT", parent_node=self))

        self.outputs.append(Socket(name="Rotation", socket_type="ROTATION", direction="OUTPUT", parent_node=self))

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 1

        return [], [input_vars[0]]
