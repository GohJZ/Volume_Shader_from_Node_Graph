import time
import pyglet
from pyglet.gl import glViewport, GL_TRIANGLES

from shaders import load_program
from geometry import make_fullscreen_quad
from camera import Camera

from pathlib import Path
from pyglet.window import key, mouse
from pyglet.graphics.shader import ShaderException

import subprocess
import sys
import tkinter as tk
from tkinter import filedialog


class ShaderApp(pyglet.window.Window):
    def __init__(self, width=800, height=600, title="Raymarch Viewer"):
        super().__init__(width, height, title, resizable=True)
        self.shader_dir = Path(__file__).parent / "shaders"
        self.sdf_path = self.shader_dir / "sdf.glsl"

        self.sdf_mtime = None
        self.program = load_program(
            self.shader_dir / "quad.vert",
            self.shader_dir / "raymarch.frag",
            self.sdf_path,
        )
        self.vertex_list = make_fullscreen_quad(self.program)
        self.camera = Camera()
        self.start_time = time.time()
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_down = False
        self.click_x = 0
        self.click_y = 0

        self.paused = False
        self.elapsed_time = 0.0
        # Store the initial file timestamp so the first check does not reload unnecessarily.
        self.sdf_mtime = self.sdf_path.stat().st_mtime_ns

        # Check the generated SDF periodically without blocking the render loop.
        pyglet.clock.schedule_interval(self.check_sdf_file, 0.25)

        pyglet.clock.schedule_interval(self.update, 1 / 120)

        # Keep the button in the bottom-left corner of the viewer.
        self.open_button = pyglet.shapes.Rectangle(12, 12, 130, 34, color=(45, 65, 85))
        self.open_label = pyglet.text.Label(
            "Open 3MF",
            x=77,
            y=29,
            anchor_x="center",
            anchor_y="center",
            font_size=12,
        )

    def on_draw(self):
        self.clear()
        self.program.use()

        self.program["iCameraPosition"] = self.camera.position
        self.program["iCameraTarget"] = tuple(self.camera.target)

        self.program["iMouse"] = (
            self.mouse_x,
            self.mouse_y,
            self.click_x if self.mouse_down else 0.0,
            self.click_y if self.mouse_down else 0.0,
        )
        self.program["iResolution"] = (float(self.width), float(self.height))
        self.vertex_list.draw(GL_TRIANGLES)

        # Draw the button over the scene using pyglet's own shaders.
        self.program.stop()
        self.open_button.draw()
        self.open_label.draw()

    def update(self, dt):
        if not self.paused:
            self.elapsed_time += dt

        speed = 15.0 * dt
        target = self.camera.target

        if self.keys[key.W] or self.keys[key.UP]:
            target[2] -= speed

        if self.keys[key.S] or self.keys[key.DOWN]:
            target[2] += speed

        if self.keys[key.A] or self.keys[key.LEFT]:
            target[0] -= speed

        if self.keys[key.D] or self.keys[key.RIGHT]:
            target[0] += speed

    def open_3mf(self):
        """Choose a local 3MF and convert it with the existing exporter."""
        try:
            dialog_root = tk.Tk()
            dialog_root.withdraw()
            filename = filedialog.askopenfilename(
                title="Open implicit 3MF",
                filetypes=[("3MF files", "*.3mf"), ("All files", "*.*")],
            )
            dialog_root.destroy()
            if not filename:
                return

            # Reuse the CLI and the Python environment running this viewer.
            exporter = self.shader_dir.parent.parent / "generate_glsl_from_3mf.py"
            subprocess.run(
                [sys.executable, str(exporter), filename, "-o", str(self.sdf_path)],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError) as error:
            # Show the exporter or picker error without closing the viewer.
            print(f"Could not open 3MF: {getattr(error, 'stderr', None) or error}")
            return

        # The existing reload method compiles and displays the new shader.
        self.switch_to()
        self.check_sdf_file(0)

    def check_sdf_file(self, _dt):
        try:
            current_mtime = self.sdf_path.stat().st_mtime_ns
        except FileNotFoundError:
            return

        # Avoid recompiling when the external file has not changed.
        if current_mtime == self.sdf_mtime:
            return

        try:
            new_program = load_program(
                self.shader_dir / "quad.vert",
                self.shader_dir / "raymarch.frag",
                self.sdf_path,
            )
            new_vertex_list = make_fullscreen_quad(new_program)
        except (OSError, ValueError, ShaderException) as error:
            # Keep rendering the previous valid shader if generated GLSL is invalid.
            print(f"Shader reload failed: {error}")
            return

        # Replace both objects because the vertex list belongs to the old program.
        self.program = new_program
        self.vertex_list = new_vertex_list
        self.sdf_mtime = current_mtime

        print("SDF shader reloaded.")

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse_x = x
        self.mouse_y = y

        # Only orbit when the drag started on the scene.
        if buttons & mouse.LEFT and self.mouse_down:
            self.camera.orbit(dx * 0.3, -dy * 0.3)

    def on_resize(self, width, height):
        glViewport(0, 0, width, height)
        return pyglet.event.EVENT_HANDLED

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.zoom(scroll_y * 2.0)

    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse_x = x
        self.mouse_y = y

        if button == mouse.LEFT:
            self.mouse_down = True
            self.click_x = x
            self.click_y = y

            # A button click should not start a camera drag.
        if button == mouse.LEFT and (x, y) in self.open_button:
            self.mouse_down = False
            self.open_3mf()
            return pyglet.event.EVENT_HANDLED

    def on_mouse_release(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.mouse_down = False

    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.paused = not self.paused

        elif symbol == key.R:
            self.camera = Camera()
            self.elapsed_time = 0.0
