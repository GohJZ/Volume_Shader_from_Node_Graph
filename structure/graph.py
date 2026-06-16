from collections import deque

class Graph:
    """
    A graph class that represents a node graph.
    It contains a list of nodes and methods to add nodes and connect them together.
    """
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        self.nodes.append(node)

    def connect(self, output_socket, input_socket):
        output_socket.connect(input_socket)

    def get_dependencies(self, node):
        dependencies = set()
        for input_socket in node.inputs:
            for connected_socket in input_socket.connected_sockets:
                dependencies.add(connected_socket.parent_node)
        return dependencies

    # reverse of get_dependencies, get all nodes that depend on the given node
    def get_dependents(self, node):
        dependents = set()
        for output_socket in node.outputs:
            for connected_socket in output_socket.connected_sockets:
                dependents.add(connected_socket.parent_node)
        return dependents

    # topological sort with Kahn's algorithm
    def topological_sort(self):
        in_degree = {node: 0 for node in self.nodes}

        for node in self.nodes:
            in_degree[node] = len(self.get_dependencies(node))

        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        sorted_nodes = []

        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)

            for dependent_node in self.get_dependents(node):
                in_degree[dependent_node] -= 1
                if in_degree[dependent_node] == 0:
                    queue.append(dependent_node)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Graph has a cycle")

        return sorted_nodes

    def __repr__(self):
        return f"Graph(nodes={self.nodes})"