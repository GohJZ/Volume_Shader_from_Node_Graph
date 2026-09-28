from pyglet.graphics.shader import Shader, ShaderProgram


def load_program(vert_path, frag_template_path, sdf_path):
    # with open(vert_path) as f:
    #     vert_src = f.read()
    # with open(frag_path) as f:
    #     frag_src = f.read()

    # vert_shader = Shader(vert_src, "vertex")
    # frag_shader = Shader(frag_src, "fragment")
    # return ShaderProgram(vert_shader, frag_shader)

    # Read the static vertex and fragment shader files.
    with open(vert_path, encoding="utf-8") as file:
        vert_src = file.read()

    with open(frag_template_path, encoding="utf-8") as file:
        frag_src = file.read()

    # Insert the latest generated SDF function into the fragment shader.
    with open(sdf_path, encoding="utf-8") as file:
        sdf_src = file.read()

    marker = "////__SDF_FUNCTION__////"

    if marker not in frag_src:
        raise ValueError("SDF placeholder is missing from the fragment shader.")

    frag_src = frag_src.replace(marker, sdf_src)

    vert_shader = Shader(vert_src, "vertex")
    frag_shader = Shader(frag_src, "fragment")

    return ShaderProgram(vert_shader, frag_shader)
