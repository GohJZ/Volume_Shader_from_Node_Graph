from structure.node import Node
from structure.socket import Socket

class RotateVectorNode(Node):
    
    def __init__(self):
        super().__init__()

        # Define the input sockets
        vector_socket = Socket(name="Vector", socket_type="VEC3", direction="INPUT", parent_node=self)
        rotation_socket = Socket(name="Rotation", socket_type="ROTATION", direction="INPUT", parent_node=self)
        self.inputs.append(vector_socket)
        self.inputs.append(rotation_socket)

        # Define the output socket
        output_socket = Socket(name="OutputVector", socket_type="VEC3", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)

    def generate_glsl(self, output_vars, input_vars):
        assert len(input_vars) == 2, "RotateVectorNode expects exactly two input variables."
        
        vector, rotation = input_vars

        # Generate the GLSL code for rotation matrix based on input rotation angles (in radians)
        rx = f"{rotation}.x"
        ry = f"{rotation}.y"
        rz = f"{rotation}.z"

        cx = f"cos({rx})"
        sx = f"sin({rx})"
        cy = f"cos({ry})"
        sy = f"sin({ry})"
        cz = f"cos({rz})"
        sz = f"sin({rz})"

        rotation_matrix = (
            f"mat3("
            f"vec3({cy}*{cz}, {cy}*{sz}, -{sy}), "
            f"vec3({cz}*{sx}*{sy} - {cx}*{sz}, "
                 f"{sx}*{sy}*{sz} + {cx}*{cz}, "
                 f"{sx}*{cy}), "
            f"vec3({cx}*{cz}*{sy} + {sx}*{sz}, "
                 f"{cx}*{sy}*{sz} - {cz}*{sx}, "
                 f"{cx}*{cy})"
            f")"
        )

        return [], [f"{rotation_matrix} * {vector}"]
