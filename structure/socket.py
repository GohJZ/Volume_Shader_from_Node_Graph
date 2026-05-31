class Socket:
    """
    Input and output sockets for nodes in a node graph. 
    Each socket has a name, type, direction (input or output), reference to the parent node it belongs to and
    a list of connected sockets.
    """
    def __init__(self, name, socket_type, direction, parent_node):
        self.name = name
        self.socket_type = socket_type
        self.direction = direction
        self.parent_node = parent_node
        self.connected_sockets = []

    def __repr__(self):
        return f"Socket(name={self.name}, type={self.socket_type}, direction={self.direction}, parent_node={self.parent_node.id})"

    # Validate that the socket types are compatible for connection
    def validate_connection(self, other_socket):
        if self.socket_type != other_socket.socket_type:
            raise ValueError(f"Cannot connect sockets of different types: {self.socket_type} and {other_socket.socket_type}.")

    # Connect this socket to another socket, ensuring connection validity and that the direction of the connection is correct
    def connect(self, other_socket):
        self.validate_connection(other_socket)

        if self.direction == 'OUTPUT' and other_socket.direction == 'INPUT':
            if other_socket not in self.connected_sockets:
                self.connected_sockets.append(other_socket)
                other_socket.connected_sockets.append(self)
        elif self.direction == 'INPUT' and other_socket.direction == 'OUTPUT':
            if other_socket not in self.connected_sockets:
                self.connected_sockets.append(other_socket)
                other_socket.connected_sockets.append(self)
        else:
            raise ValueError("Can only connect an output socket to an input socket.")