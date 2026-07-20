from __future__ import annotations

from pathlib import Path
import sys

from generator.cli import main as cli_main
from generator.desktop_launcher import DEFAULT_LAUNCHER_WORKSPACE, launch_desktop


def _editor_arguments(source: str) -> list[str]:
    identity = Path(source).stem or "imported-modpack"
    workspace = DEFAULT_LAUNCHER_WORKSPACE / "workspaces" / identity
    return [
        "quest-editor-serve",
        source,
        "--workspace",
        workspace.as_posix(),
        "--port",
        "0",
    ]


def main(argv: list[str] | None = None) -> int:
    """Run the native app, its frozen child commands, or a dropped modpack path."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    # The desktop launcher starts the editor through sys.executable. In a
    # PyInstaller build that executable is FTBQuestMaker.exe rather than a
    # Python interpreter, so explicitly dispatch the frozen ``-m generator``
    # child invocation instead of recursively reopening the launcher.
    if arguments[:2] == ["-m", "generator"]:
        return cli_main(arguments[2:])

    # Windows passes a dropped file/folder to the executable as argv[1]. This
    # makes dragging a .zip/.mrpack or instance directory onto the app useful.
    if len(arguments) == 1 and Path(arguments[0]).exists():
        return cli_main(_editor_arguments(arguments[0]))

    if arguments:
        return cli_main(arguments)
    return launch_desktop()


if __name__ == "__main__":  # pragma: no cover - native executable entrypoint
    raise SystemExit(main())
