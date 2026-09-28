"""Export the sphere's raw field to GLSL (no bounds or transforms yet)."""

import argparse
from pathlib import Path

import lib3mf

from glsl_generator import GLSLGenerator
from three_mf_importer import ThreeMFImporter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input implicit 3MF file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path(__file__).parent / "shadertoy_app" / "shaders" / "sdf.glsl",
    )

    args = parser.parse_args()

    try:
        # Do not overwrite the input package with shader text.
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files.")

        # Follow the same import -> selected socket -> generator flow as Blender.
        context = ThreeMFImporter().import_file(args.input)
        output_socket = next(iter(context.named_outputs.values()))
        glsl = GLSLGenerator().generate_function(context.graph, output_socket, "sdf")

        print(glsl)

        # Save the generator's text unchanged; keep generated files in .user by default.
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(glsl, encoding="utf-8")
    except (OSError, ValueError, NotImplementedError, lib3mf.ELib3MFException) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Saved raw field to {args.output}")


if __name__ == "__main__":
    main()
