from structure.node import Node
from structure.socket import Socket

class BoxNode(Node):
    """
    A node that represents a box in a node graph. 
    It has parameters for the size and position of the box.
    """
    def __init__(self, size=(1.0, 1.0, 1.0), position=(0.0, 0.0, 0.0)):
        super().__init__(parameters={"size": size, "position": position})

        # Define the output sockets
        output_socket = Socket(name="BoxSDF", socket_type="SDF", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)
    
    def __repr__(self):
        return f"BoxNode(id={self.id}, size={self.parameters['size']}, position={self.parameters['position']})"

    # Generate GLSL code for the box SDF and variable name for the result
    def generate_glsl(self, p_var="p"):
        size = self.parameters['size']
        position = self.parameters['position']

        result_var = f"sdf_{self.id[:8]}"
        code = f"""vec3 q = abs({p_var} - vec3{position}) - vec3{size};
float {result_var} = length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);"""

        return code, result_var