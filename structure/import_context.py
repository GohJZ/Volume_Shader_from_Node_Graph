from .graph import Graph

class ImportContext:
    """
    Context for importing a Blender node graph into an IR graph.
    It packages all the states and mappings needed during the import process.
    Graph and socket_map are shared across recursion, but 
    parent_inputs and group_outputs represent current recursion level.
    """

    def __init__(self):
        self.graph = Graph()

        # Blender socket -> IR socket
        self.socket_map = {}

        # Used when importing a node group. 
        # Node group input sockets -> IR sockets in the parent graph
        self.parent_inputs = {}

        # Used when leaving a node group. 
        # Node group output sockets -> IR sockets in the parent graph
        self.group_outputs = {}

        # Selects output socket from caller
        self.named_outputs = {}