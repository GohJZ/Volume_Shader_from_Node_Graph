from structure.graph import Graph
from nodes import SphereNode, BoxNode, UnionNode


class BlenderImporter:
    """
    A class that translates a Blender node graph representation into the internal node graph structure.
    """

    def __init__(self):
        self.graph = Graph()
        self.node_map = {} # Maps Blender nodes to IR nodes
        self.node_importers = {
                "SDF_Sphere": self.import_sphere,
                "SDF_Box" : self.import_box,
                "SDF_Union" : self.import_union
            }
        self.socket_map = {} # Maps Blender sockets to IR sockets

    def import_graph(self, node_tree):
        """
        Imports a Blender node graph into the internal representation.
        Steps:
            1. Find blender node tree.
            2. Create IR nodes for each Blender node.
            3. Connect IR nodes based on Blender node connections.
            4. Return the constructed IR graph.
        """
        # Reset the graph and node map for each import
        self.graph = Graph()
        self.node_map = {}
        self.socket_map = {}

        # Step 1: Find Blender node tree
        blender_nodes = node_tree.nodes
        blender_links = node_tree.links

        # Step 2: Create IR nodes for each Blender node
        for blender_node in blender_nodes:
            ir_node = self.create_ir_node(blender_node)

            if ir_node is not None:
                self.graph.add_node(ir_node)
                self.node_map[blender_node] = ir_node

        # Step 3: Connect IR nodes based on Blender node connections
        for link in blender_links:
            ir_from = self.socket_map.get(link.from_socket)
            ir_to = self.socket_map.get(link.to_socket)

            if ir_from is None or ir_to is None:
                continue

            self.graph.connect(ir_from, ir_to)
        # Step 4: Return the constructed IR graph
        return self.graph

    def create_ir_node(self, blender_node):
        if not hasattr(blender_node, "node_tree"):
            return None

        node_name = blender_node.node_tree.name

        importer = self.node_importers.get(node_name)

        if importer is None:
            return None

        return importer(blender_node)

    def import_sphere(self, blender_node):
        sphere_node = SphereNode(radius=float(blender_node.inputs['Radius'].default_value), position = tuple(blender_node.inputs["Center"].default_value))
        self.socket_map[blender_node.outputs['Distance']] = sphere_node.outputs[0]
        return sphere_node

    def import_box(self, blender_node):
        box_node = BoxNode(size=tuple(blender_node.inputs['Size'].default_value), position = tuple(blender_node.inputs["Center"].default_value))
        self.socket_map[blender_node.outputs['Distance']] = box_node.outputs[0]
        return box_node

    def import_union(self, blender_node):
        union_node = UnionNode()
        self.socket_map[blender_node.inputs['A']] = union_node.inputs[0]
        self.socket_map[blender_node.inputs['B']] = union_node.inputs[1]
        self.socket_map[blender_node.outputs['Distance']] = union_node.outputs[0]
        return union_node

