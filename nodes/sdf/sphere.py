from structure.node import Node
from structure.socket import Socket

class SphereNode(Node):
    """
    A node that represents a sphere in a node graph. 
    It has parameters for the radius and position of the sphere.
    """
    def __init__(self, radius=1.0, position=(0.0, 0.0, 0.0)):
        super().__init__(parameters={"radius": radius, "position": position})

        # Define the output sockets
        output_socket = Socket(name="SphereSDF", socket_type="SDF", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)
    
    def __repr__(self):
        return f"SphereNode(id={self.id}, radius={self.parameters['radius']}, position={self.parameters['position']})"

    # Generate GLSL code for the sphere SDF and variable name for the result
    def generate_glsl(self, p_var="p"):
        radius = self.parameters['radius']
        position = self.parameters['position']

        result_var = f"sdf_{self.id[:8]}"
        code = f"float {result_var} = length({p_var} - vec3{position}) - {radius};"
        
        return code, result_var