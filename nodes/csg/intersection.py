from structure.node import Node
from structure.socket import Socket

class IntersectionNode(Node):
    """
    A node that represents the intersection of two SDFs in a node graph. 
    It takes two SDF inputs and outputs their intersection.
    """
    def __init__(self):
        super().__init__(parameters=None)

        # Define the input sockets
        input_socket1 = Socket(name="SdfInput1", socket_type="SDF", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket1)
        input_socket2 = Socket(name="SdfInput2", socket_type="SDF", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket2)
        
        # Define the output socket
        output_socket = Socket(name="IntersectionOutput", socket_type="SDF", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)
    
    def __repr__(self):
        return f"IntersectionNode(id={self.id})"
    
    # Generate GLSL code for the intersection of two SDFs and variable name for the result
    def generate_glsl(self, output_var, sdf1_var="sdf1", sdf2_var="sdf2"):
        expression = f"max({sdf1_var}, {sdf2_var})"
        return [], expression
