"""The Joi scene: K's rooftop, at night and in the rain, with a giant hologram of JOI.

Everything is defined in reference-frame coordinates (200x83 pixels, the same scale JOI's sprite was extracted at)
and multiplied by the terminal's scale. The film frame sits in the middle of the terminal and, if the terminal is
taller than 2.4:1, the city fills the rest.

Scene only composes the layers. The base (fog, buildings, floor, canopy) is built once per size, with fixed
seeds; each frame is a function of the tick: it copies the base and paints the lights, ships, hologram, K and
rain on top.
"""

from __future__ import annotations

import random

from modules.core.color import Frame
from modules.graphics.canvas import Canvas
from modules.scene import background
from modules.scene.canopy import Canopy
from modules.scene.city import City
from modules.scene.hologram import Hologram
from modules.scene.k import K
from modules.scene.layout import k_scale
from modules.scene.puddles import Puddles
from modules.scene.rain import Rain
from modules.scene.rooftop import Rooftop


class Scene:
    def __init__(self, columns: int, height: int) -> None:
        """columns x height in terminal pixels (2 pixels per text row).

        The build order matters: each step paints over the previous ones on the base, and the city's steps
        share one RNG, so reordering them changes the skyline.
        """
        self.canvas = canvas = Canvas(columns, height)
        rng, city_rng = random.Random(2049), random.Random(2050)
        background.paint_fog(canvas)
        self.city = City(canvas)
        self.city.build_towers(city_rng)
        background.paint_floor(canvas)
        background.quantize(canvas)
        self.city.build_neons(city_rng)
        self.city.build_windows(city_rng)
        self.city.build_balcony()
        self.rooftop = Rooftop(canvas)
        self.canopy = Canopy(canvas, k_scale(canvas))
        self.city.build_footer()
        self.puddles = Puddles(canvas)
        self.city.build_ships(city_rng)
        self.city.build_bokeh(city_rng)
        self.hologram = Hologram(canvas)
        self.k = K(canvas, k_scale(canvas), self.puddles)
        self.rain = Rain(canvas, self.canopy, self.puddles, rng)

    def pixels(self, tick: int) -> Frame:
        """The scene's frame (h rows x w columns), without the black side bars. Layers paint back to front."""
        frame = self.canvas.new_frame(tick)
        self.city.paint(frame, tick)
        self.hologram.paint(frame, tick)
        ripples = self.rain.ripples(tick)
        self.puddles.reflect(frame, tick, ripples)
        self.rooftop.paint(frame, tick)
        self.k.paint(frame, tick, self.hologram.pulse(tick))
        self.canopy.paint(frame, tick)
        self.rain.paint(frame, tick)
        self.puddles.paint_ripples(frame, ripples)
        return frame

    def frame(self, tick: int) -> Frame:
        """The whole terminal's frame: the scene, with black bars on the sides if the terminal is too wide."""
        return self.canvas.letterbox(self.pixels(tick))
