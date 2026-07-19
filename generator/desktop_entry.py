from __future__ import annotations

from generator.desktop_launcher import launch_desktop


def main() -> int:
    return launch_desktop()


if __name__ == "__main__":  # pragma: no cover - native executable entrypoint
    raise SystemExit(main())
