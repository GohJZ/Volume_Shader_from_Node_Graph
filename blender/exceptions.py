class UnsupportedBlenderNodeError(Exception):
    # Raised when a Blender node has no corresponding importer.
    
    def __init__(self, node):

        self.node = node

        super().__init__(
            f"Unsupported Blender node:\n"
            f"  Type: {node.bl_idname}\n"
            f"  Name: {node.name}"
        )