#!/usr/bin/env python3
"""K on the rooftop, looking at JOI: the Blade Runner 2049 scene as pixel art in the terminal.

    python3 br.py

Ctrl+C quits. The terminal needs to be at least 60x16 and looks best at 200x50 or larger.
"""

from modules.scene import Scene
from modules.terminal.loop import run_loop


def main() -> None:
    run_loop(Scene)


if __name__ == "__main__":
    main()
