from structure import graph
from structure.socket import Socket
from structure.graph import Graph
from nodes import SphereNode, BoxNode, UnionNode
import glsl_generator

# IR graph test
sphere = SphereNode(radius=1, position=(-1,0,0))
box = BoxNode(size=(0.8,0.6,1), position=(0,0,0))
union = UnionNode()

# Test graph dependencies
graph = Graph()
graph.add_node(union)
graph.add_node(sphere)
graph.add_node(box)

graph.connect(sphere.outputs[0], union.inputs[0])
graph.connect(box.outputs[0], union.inputs[1])

# Test GLSL code generation
generator = glsl_generator.GLSLGenerator()
glsl_code = generator.generate_code(graph)
print("Generated GLSL code:")
print(glsl_code)