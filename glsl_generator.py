class GLSLGenerator:
    """
    A class that generates GLSL code from a node graph. 
    It takes a topological-sorted graph as input and produces GLSL code that represents the operations defined by the nodes in the graph. 
    Variable naming is handled to ensure that each node's output is uniquely identifiable in the generated code.
    """
    def __init__(self):
        self.var_counter = 0
        self.node_to_var = {}

    def get_var_name(self):
        var_name = f"sdf_{self.var_counter}"
        self.var_counter += 1
        return var_name

    def generate_code(self, graph):\
        # in the case where multiply graphs use the same generator (if needed)
        #self.var_counter = 0
        #self.node_to_var = {}

        sorted_nodes = graph.topological_sort()
        code_lines = []

        for node in sorted_nodes:
            var_name = self.get_var_name()
            self.node_to_var[node] = var_name
            
            # gather input variable names from connected nodes
            input_vars = []
            for input_socket in node.inputs:
                if len(input_socket.connected_sockets) != 1:
                    raise ValueError(f"Input socket {input_socket} must be connected to exactly one output socket.")

                for connected_socket in input_socket.connected_sockets:
                    connected_node = connected_socket.parent_node
                    if connected_node in self.node_to_var:
                        input_vars.append(self.node_to_var[connected_node])
                    else:
                        raise ValueError(f"Connected node {connected_node} has not been assigned a variable name yet.")
                
            # generate GLSL code for the current node using its generate_glsl method
            # temperory names will eventually need unique names too! 
            temps, expression = node.generate_glsl(var_name, *input_vars)
            code_lines.extend(temps)
            code_lines.append(f"float {var_name} = {expression};")

        return "\n".join(code_lines)




