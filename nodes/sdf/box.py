from structure.node import Node
from structure.socket import Socket
from helper import HelperFunctions

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
    def generate_glsl(self, output_var, p_var="p"):
        size = self.parameters['size']
        position = self.parameters['position']
        q_var = f"{output_var}_q"

        temp = [f"vec3 {q_var} = abs({p_var} - {HelperFunctions.format_vec3(position)}) - ({HelperFunctions.format_vec3(size)});"]
        expression = f"length(max({q_var}, 0.0)) + min(max({q_var}.x, max({q_var}.y, {q_var}.z)), 0.0)"

        return temp, expression