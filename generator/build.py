from pathlib import Path

from generator.config import OUTPUT
from generator.log import Level, log
from generator.version import VERSION


def build() -> None:
    log(Level.INFO, f"Immersive Adventure Neo Quest Builder {VERSION}")

    OUTPUT.mkdir(exist_ok=True)

    log(Level.SUCCESS, "Output directory ready.")
    log(Level.SUCCESS, "Build completed successfully.")


if __name__ == "__main__":
    build()