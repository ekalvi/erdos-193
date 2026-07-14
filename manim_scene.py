"""
Manim (3b1b-style) render of the amplification construction — real data.

Levels 0..3 of the record run: each round the walk morphs to its enlarged &
twisted position (blue skeleton), then the new generation's walk draws itself
along it (green-tinged). Ambient camera rotation throughout.

Render:  .venv-manim/bin/manim -ql manim_scene.py Amplify   (test, 480p)
         .venv-manim/bin/manim -qh manim_scene.py Amplify   (final, 1080p)
"""
import json
import numpy as np
from manim import (
    ThreeDScene, VMobject, DEGREES, BLUE_D, GREEN_C, GREY_B, WHITE,
    Create, Transform, FadeOut, FadeIn, Text, config,
)

DATA = json.load(open("viz/walk3d-data.json"))
M = np.array(DATA["M"])
LEVELS = [np.array(l["points"], dtype=float) for l in DATA["levels"][:4]]


def normalize(points, spread=5.5):
    c = points.mean(axis=0)
    r = np.abs(points - c).max() or 1.0
    return (points - c) / r * spread


def polyline(points, color, width=3.0, opacity=0.9):
    m = VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity)
    m.set_points_as_corners([np.array(p) for p in points])
    return m


class Amplify(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        self.begin_ambient_camera_rotation(rate=0.06)

        title = Text("Enlarge. Twist. Stitch. Repeat.", font="Outfit", font_size=30)
        self.add_fixed_in_frame_mobjects(title)
        title.to_edge(np.array([0.0, 1.0, 0.0])).shift([0, -0.2, 0])
        self.play(FadeIn(title), run_time=1)

        walk = polyline(normalize(LEVELS[0]), BLUE_D, 4.0)
        self.play(Create(walk), run_time=2.5)
        self.wait(0.5)

        for k in range(1, len(LEVELS)):
            # morph: current level flies to its enlarged+twisted image
            enlarged = LEVELS[k - 1] @ M.T
            target = polyline(normalize(enlarged), GREY_B, 2.5, 0.8)
            self.play(Transform(walk, target), run_time=2.2)
            # stitch: the new generation draws itself along the skeleton
            new_walk = polyline(normalize(LEVELS[k]), BLUE_D if k % 2 else GREEN_C, 3.0)
            self.play(Create(new_walk), run_time=3.2)
            self.play(FadeOut(walk), run_time=0.5)
            walk = new_walk
            self.wait(0.4)

        outro = Text("28,271 verified steps — no three in a line", font="Outfit", font_size=26)
        self.add_fixed_in_frame_mobjects(outro)
        outro.to_edge(np.array([0.0, -1.0, 0.0]))
        self.play(FadeIn(outro), run_time=1)
        self.wait(2.5)
