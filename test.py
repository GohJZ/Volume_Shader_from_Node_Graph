from structure import graph
from structure.socket import Socket
from structure.graph import Graph
from nodes import SphereNode, BoxNode, UnionNode
import glsl_generator

# IR graph test
sphere = SphereNode(radius=1, position=(-1,0,0))
box = BoxNode()
union = UnionNode()

# s1= sphere.generate_glsl()
# b1 = box.generate_glsl()
# u1 = union.generate_glsl(s1, b1)

# sphere.outputs[0].connect(union.inputs[0])
# box.outputs[0].connect(union.inputs[1])

# # Test code generation and variable naming
# print(f"Sphere: {s1}")
# print(f"Box: {b1}")
# print(f"Union: {u1}")
# print()

# # Test socket connections
# print(f"Sphere connected sockets: {sphere.outputs[0].connected_sockets}")
# print(f"Box connected sockets: {box.outputs[0].connected_sockets}")
# print(f"Union input 0 connected sockets: {union.inputs[0].connected_sockets}")
# print(f"Union input 1 connected sockets: {union.inputs[1].connected_sockets}")
# print(f"Union input in Sphere output?: {union.inputs[0] in sphere.outputs[0].connected_sockets}")
# print(f"Sphere output in Union input?: {sphere.outputs[0] in union.inputs[0].connected_sockets}")
# print()

# Test invalid connection
#vec_socket = Socket(name="Position",socket_type="VEC3",direction="INPUT",parent_node=sphere)
#sphere.outputs[0].connect(vec_socket)

# Test graph dependencies
graph = Graph()
graph.add_node(union)
graph.add_node(sphere)
graph.add_node(box)

graph.connect(sphere.outputs[0], union.inputs[0])
graph.connect(box.outputs[0], union.inputs[1])

# print(f"Union dependencies: {graph.get_dependencies(union)}")
# print(f"Sphere dependents: {graph.get_dependents(sphere)}")

# sorted_nodes = graph.topological_sort()
# for node in sorted_nodes:
#     print(node)
# print()

# Test GLSL code generation
generator = glsl_generator.GLSLGenerator()
glsl_code = generator.generate_code(graph)
print("Generated GLSL code:")
print(glsl_code)