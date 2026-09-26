"""The Blade Runner scene, split in layers. Dependencies only point inward:

    core        colors, frames and time: pure functions, imports nothing from the project
    graphics    the pixel canvas and sprite scaling (core)
    characters  K and JOI as data and behavior: sprites, the smoking loop, the blink (core)
    scene       paints the rooftop, the city, JOI, K and the rain onto the canvas (core, graphics, characters)
    terminal    turns frames into ANSI and runs the render loop (core); it knows nothing about the scene

br.py, at the project root, is the only place that wires scene and terminal together.
"""
