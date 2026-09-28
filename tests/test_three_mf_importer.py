"""Basic checks for the 3MF importer and export script."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from glsl_generator import GLSLGenerator
from three_mf_importer import ThreeMFImporter, iter_items


PROJECT = Path(__file__).resolve().parents[1]
EXAMPLES = PROJECT / "resources" / "output" / "3mf"
EXPORT_SCRIPT = PROJECT / "generate_glsl_from_3mf.py"


class ThreeMFImporterTests(unittest.TestCase):
    def test_sphere_equation(self):
        # The sphere has radius 20, so its field should be length(p) - 20.
        context = ThreeMFImporter().import_file(EXAMPLES / "01_sphere.3mf")
        result = context.named_outputs["shape"]
        glsl = GLSLGenerator().generate_function(context.graph, result)
        self.assertIn("return (length(p) - 20.000);", glsl)

    def test_all_examples_generate_glsl(self):
        # Check all 13 numbered examples and the selected box in basics.
        paths = sorted(EXAMPLES.glob("[0-9][0-9]_*.3mf"))
        paths.append(EXAMPLES / "basics.3mf")
        self.assertEqual(len(paths), 14)

        for path in paths:
            # Show the filename if one example fails.
            with self.subTest(file=path.name):
                context = ThreeMFImporter().import_file(path)
                result = next(iter(context.named_outputs.values()))
                self.assertEqual(result.socket_type, "FLOAT")

                # Every input should have one connection of the same type.
                for node in context.graph.nodes:
                    for socket in node.inputs:
                        self.assertEqual(len(socket.connected_sockets), 1)
                        source = socket.connected_sockets[0]
                        self.assertEqual(socket.socket_type, source.socket_type)

                glsl = GLSLGenerator().generate_function(context.graph, result)
                self.assertIn("float sdf(vec3 p)", glsl)
                self.assertIn("return ", glsl)

    def test_basics_function_arguments(self):
        # The called box function receives center (5, 5, 5) and size (10, 10, 10).
        context = ThreeMFImporter().import_file(EXAMPLES / "basics.3mf")
        result = context.named_outputs["shape"]
        glsl = GLSLGenerator().generate_function(context.graph, result)
        self.assertIn("abs((p - vec3(5.000, 5.000, 5.000)))", glsl)
        self.assertIn("vec3(10.000, 10.000, 10.000)", glsl)
        # The box calculation multiplies its full size by 0.5.
        self.assertIn("vec3(0.500, 0.500, 0.500)", glsl)

    def test_renamed_nodes_and_channel(self):
        # Rename the nodes and their references in a temporary copy.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "renamed.3mf"
            with (
                ZipFile(EXAMPLES / "01_sphere.3mf") as source,
                ZipFile(path, "w") as target,
            ):
                for entry in source.infolist():
                    data = source.read(entry.filename)
                    if entry.filename.endswith(".model"):
                        for old, new in (
                            (b"sphere_length", b"node42"),
                            (b"sphere_radius", b"node17"),
                            (b"sphere_distance", b"node9"),
                            (b"shape", b"distance"),
                        ):
                            data = data.replace(old, new)
                    target.writestr(entry, data)

            # Different names should still produce the same sphere equation.
            context = ThreeMFImporter().import_file(path)
            self.assertEqual(list(context.named_outputs), ["distance"])
            result = context.named_outputs["distance"]
            glsl = GLSLGenerator().generate_function(context.graph, result)
            self.assertIn("return (length(p) - 20.000);", glsl)


class ThreeMFExportTests(unittest.TestCase):
    def setUp(self):
        # Keep exported files in a separate folder for each test.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)

    def run_export(self, source, output):
        # Always give an output path so the viewer's shader is left alone.
        return subprocess.run(
            [sys.executable, str(EXPORT_SCRIPT), str(source), "-o", str(output)],
            cwd=self.folder,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_export_sphere(self):
        # Check that the script creates the output folder and writes the GLSL.
        output = self.folder / "shaders" / "sphere.glsl"
        result = self.run_export(EXAMPLES / "01_sphere.3mf", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        glsl = output.read_text(encoding="utf-8")
        self.assertIn("float sdf(vec3 p)", glsl)
        self.assertIn("return (length(p) - 20.000);", glsl)

    def test_invalid_files(self):
        # Neither a missing file nor a broken package should write a shader.
        output = self.folder / "sdf.glsl"
        invalid = self.folder / "invalid.3mf"
        invalid.write_text("This is not a 3MF package.", encoding="utf-8")
        for source in (self.folder / "missing.3mf", invalid):
            with self.subTest(file=source.name):
                result = self.run_export(source, output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())

    def test_input_is_not_overwritten(self):
        # Use a copy when passing the same path as both input and output.
        source = self.folder / "sphere.3mf"
        original = (EXAMPLES / "01_sphere.3mf").read_bytes()
        source.write_bytes(original)
        result = self.run_export(source, source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("different files", result.stderr)
        self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
