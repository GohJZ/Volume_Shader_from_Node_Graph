from uuid import uuid4

class Node:
    """
    A generic node class that can be used to create a node graph.
    Each node has a unique identifier, a list of input and output sockets, and a dictionary of parameters.
    """
    def __init__(self, parameters=None):
        self.id = str(uuid4())
        self.inputs = []
        self.outputs = []
        self.parameters = parameters if parameters is not None else {}
        self.is_constant = False

    def __repr__(self):
        return f"Node(id={self.id}, inputs={self.inputs}, outputs={self.outputs}, parameters={self.parameters})"
