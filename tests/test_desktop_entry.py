from pathlib import Path

import generator.desktop_entry as desktop_entry


def test_frozen_generator_child_command_is_dispatched(monkeypatch) -> None:
    captured = []
    monkeypatch.setattr(desktop_entry, "cli_main", lambda argv: captured.append(argv) or 17)
    assert desktop_entry.main(["-m", "generator", "quest-editor-serve", "pack.zip"]) == 17
    assert captured == [["quest-editor-serve", "pack.zip"]]


def test_dropped_modpack_opens_editor_service(monkeypatch, tmp_path: Path) -> None:
    modpack = tmp_path / "Example Pack.mrpack"
    modpack.write_bytes(b"PK")
    captured = []
    monkeypatch.setattr(desktop_entry, "cli_main", lambda argv: captured.append(argv) or 0)
    assert desktop_entry.main([str(modpack)]) == 0
    assert captured[0][0:2] == ["quest-editor-serve", str(modpack)]
    assert captured[0][-2:] == ["--port", "0"]


def test_no_arguments_opens_desktop_launcher(monkeypatch) -> None:
    monkeypatch.setattr(desktop_entry, "launch_desktop", lambda: 9)
    assert desktop_entry.main([]) == 9
