from structure.node import Node
from structure.socket import Socket

class UnionNode(Node):
    """
    A node that represents the union of two SDFs in a node graph. 
    It takes two SDF inputs and outputs their union.
    """
    def __init__(self):
        super().__init__(parameters=None)

        # Define the input sockets
        input_socket1 = Socket(name="SdfInput1", socket_type="SDF", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket1)
        input_socket2 = Socket(name="SdfInput2", socket_type="SDF", direction="INPUT", parent_node=self)
        self.inputs.append(input_socket2)
        
        # Define the output socket
        output_socket = Socket(name="UnionOutput", socket_type="SDF", direction="OUTPUT", parent_node=self)
        self.outputs.append(output_socket)
    
    def __repr__(self):
        return f"UnionNode(id={self.id})"
    
    # Generate GLSL code for the union of two SDFs and variable name for the result
    def generate_glsl(self, sdf1_var="sdf1", sdf2_var="sdf2"):
        result_var = f"sdf_{self.id[:8]}"
        code = f"float {result_var} = min({sdf1_var}, {sdf2_var});"

        return code, result_var