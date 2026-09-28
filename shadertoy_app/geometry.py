from pyglet.gl import GL_TRIANGLES


def make_fullscreen_quad(program):
    vertices = (-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1)
    return program.vertex_list(6, GL_TRIANGLES, position=("f", vertices))
