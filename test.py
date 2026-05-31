from structure.socket import Socket
from nodes import SphereNode, BoxNode, UnionNode

# IR graph test
sphere = SphereNode(radius=1, position=(-1,0,0))
box = BoxNode()
union = UnionNode()

s1, s1_var = sphere.generate_glsl()
b1, b1_var = box.generate_glsl()
u1, u1_var = union.generate_glsl(s1_var, b1_var)

sphere.outputs[0].connect(union.inputs[0])
box.outputs[0].connect(union.inputs[1])

# Test code generation and variable naming
print(f"Sphere: {s1}, {s1_var}")
print(f"Box: {b1}, {b1_var}")
print(f"Union: {u1}, {u1_var}")
print()

# Test socket connections
print(f"Sphere connected sockets: {sphere.outputs[0].connected_sockets}")
print(f"Box connected sockets: {box.outputs[0].connected_sockets}")
print(f"Union input 0 connected sockets: {union.inputs[0].connected_sockets}")
print(f"Union input 1 connected sockets: {union.inputs[1].connected_sockets}")
print(f"Union input in Sphere output?: {union.inputs[0] in sphere.outputs[0].connected_sockets}")
print(f"Sphere output in Union input?: {sphere.outputs[0] in union.inputs[0].connected_sockets}")

# Test invalid connection
#vec_socket = Socket(name="Position",socket_type="VEC3",direction="INPUT",parent_node=sphere)
#sphere.outputs[0].connect(vec_socket)