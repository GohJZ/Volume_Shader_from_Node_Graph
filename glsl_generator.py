class GLSLGenerator:
    """
    A class that generates GLSL code from a node graph. 
    It takes a topological-sorted graph as input and produces GLSL code that represents the operations defined by the nodes in the graph. 
    Variable naming is handled to ensure that each node's output is uniquely identifiable in the generated code.
    """
    def __init__(self):
        self.var_counter = 0
        self.socket_to_expr = {}
        self.TYPE_MAP = {
            "FLOAT": "float",
            "VEC3": "vec3",
            "ROTATION": "vec3",  # Assuming rotation is represented as a vec3 for simplicity
        }

    # Generate a unique variable name for temporary variables in the GLSL code.
    def get_var_name(self):
        var_name = f"tmp_{self.var_counter}"
        self.var_counter += 1
        return var_name

    def generate_code(self, graph, output_socket):
        # Resets for each code generation in case of multiple graphs
        self.var_counter = 0
        self.socket_to_expr = {}
        final_expr = None

        # Count how many times each output socket is used as an input in the graph
        use_count = {}

        for node in graph.nodes:
            for input_socket in node.inputs:
                for connected_output in input_socket.connected_sockets:
                    use_count[connected_output] = (use_count.get(connected_output, 0) + 1)

        sorted_nodes = graph.topological_sort()
        code_lines = []

        for node in sorted_nodes:           

            # gather input expressions for the current node based on its connected output sockets
            input_expr = []

            for input_socket in node.inputs:
                if len(input_socket.connected_sockets) != 1:
                    raise ValueError(f"Input socket {input_socket} must be connected to exactly one output socket.")

                connected_output = input_socket.connected_sockets[0]

                if connected_output not in self.socket_to_expr:
                    raise ValueError(f"Connected output {connected_output} has not been assigned a variable name yet.")

                input_expr.append(self.socket_to_expr[connected_output])
                
            # Constant nodes don't need temporary variables
            if node.is_constant:
                _, expressions = node.generate_glsl([], input_expr)

                for socket, expr in zip(node.outputs, expressions):
                    self.socket_to_expr[socket] = expr

                continue

            # generate GLSL code for the current node using its generate_glsl method
            temps, expressions = node.generate_glsl([], input_expr)
            code_lines.extend(temps)

            for output_socket_ir, expr in zip(node.outputs, expressions):

                # If the current output socket is the final output socket, store its expression for the return statement
                if output_socket_ir == output_socket:
                    final_expr = expr
                    continue

                # If output only used once, store expression without temporary variable; 
                # otherwise, create a temporary variable for it
                if use_count.get(output_socket_ir, 0) == 1:
                    self.socket_to_expr[output_socket_ir] = expr

                else:
                    var = self.get_var_name()

                    glsl_type = self.TYPE_MAP[output_socket_ir.socket_type]

                    code_lines.append(f"{glsl_type} {var} = {expr};")

                    self.socket_to_expr[output_socket_ir] = var

        if final_expr is None:
            raise ValueError("No output socket was assigned a final expression.")

        return "\n".join(code_lines), final_expr

    # Generate a complete GLSL function that wraps the generated code and returns the final expression.
    def generate_function(self, graph, output_socket, function_name="sdf"):
        code, final_expr = self.generate_code(graph, output_socket)
        indented_code = self.indent_code(code)

        return (
            f"float {function_name}(vec3 p)\n"
            "{\n"
            f"{indented_code}\n"
            f"    return {final_expr};\n"
            "}"
        )

    # Indent generated GLSL code for better readability
    def indent_code(self, code, spaces=4):
        indentation = " " * spaces
        return "\n".join(indentation + line for line in code.splitlines())
