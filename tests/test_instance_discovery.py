from __future__ import annotations

import json
from pathlib import Path

import pytest

from generator.desktop_launcher import build_editor_launch_plan
from generator.instance_discovery import (
    InstanceSearchRoot,
    default_instance_roots,
    discover_modpack_instances,
)


def _jar(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PK\x03\x04fixture")


def test_discovers_common_linux_launcher_instances(tmp_path: Path) -> None:
    home = tmp_path / "home"
    _jar(home / ".minecraft/mods/vanilla-plus.jar")

    curse = home / "curseforge/minecraft/Instances/Technology"
    _jar(curse / "mods/mekanism.jar")
    (curse / "minecraftinstance.json").write_text(
        json.dumps(
            {
                "name": "Technology Pack",
                "gameVersion": "1.21.1",
                "baseModLoader": {"name": "neoforge-21.1.80"},
            }
        ),
        encoding="utf-8",
    )

    prism = home / ".local/share/PrismLauncher/instances/Magic"
    _jar(prism / ".minecraft/mods/ars.jar")
    (prism / "instance.cfg").write_text("name=Magic Pack\n", encoding="utf-8")
    (prism / "mmc-pack.json").write_text(
        json.dumps(
            {
                "components": [
                    {"uid": "net.minecraft", "version": "1.21.1"},
                    {"uid": "net.neoforged", "version": "21.1.90"},
                ]
            }
        ),
        encoding="utf-8",
    )

    modrinth = home / ".local/share/modrinth-app/profiles/Storage"
    _jar(modrinth / "mods/ae2.jar")
    (modrinth / "profile.json").write_text(
        json.dumps(
            {
                "name": "Storage Pack",
                "game_version": "1.21.1",
                "loader": "fabric",
                "loader_version": "0.16.0",
            }
        ),
        encoding="utf-8",
    )

    result = discover_modpack_instances(home=home, platform_name="linux")

    assert result.is_clean
    assert [item.name for item in result.instances] == [
        ".minecraft",
        "Magic Pack",
        "Storage Pack",
        "Technology Pack",
    ]
    by_name = {item.name: item for item in result.instances}
    assert by_name["Technology Pack"].loader == "neoforge"
    assert by_name["Magic Pack"].game_directory.endswith("/.minecraft")
    assert by_name["Storage Pack"].launcher == "Modrinth App"
    assert all(item.mod_count == 1 for item in result.instances)


def test_custom_roots_are_deduplicated_by_game_directory(tmp_path: Path) -> None:
    instance = tmp_path / "Pack"
    _jar(instance / "mods/example.jar")
    result = discover_modpack_instances(
        (
            InstanceSearchRoot("Custom A", instance),
            InstanceSearchRoot("Custom B", instance),
        )
    )
    assert len(result.instances) == 1


def test_non_instance_directories_are_ignored(tmp_path: Path) -> None:
    (tmp_path / "documents").mkdir()
    result = discover_modpack_instances((tmp_path,))
    assert result.instances == ()


def test_discovery_is_deterministic(tmp_path: Path) -> None:
    for name in ("Zeta", "Alpha"):
        _jar(tmp_path / name / "mods/example.jar")
    roots = (InstanceSearchRoot("Custom", tmp_path),)
    first = discover_modpack_instances(roots).format_json()
    second = discover_modpack_instances(roots).format_json()
    assert first == second
    assert [item.name for item in discover_modpack_instances(roots).instances] == ["Alpha", "Zeta"]


def test_editor_launch_plan_uses_discovered_game_directory(tmp_path: Path) -> None:
    instance_root = tmp_path / "Prism"
    _jar(instance_root / ".minecraft/mods/example.jar")
    result = discover_modpack_instances((InstanceSearchRoot("Prism", instance_root),))
    instance = result.instances[0]
    plan = build_editor_launch_plan(
        instance,
        workspace_root=tmp_path / "workspace",
        open_browser=False,
        python_executable="python-test",
    )
    assert plan.command[:4] == ("python-test", "-m", "generator", "quest-editor-serve")
    assert instance.game_directory in plan.command
    assert "--no-browser" in plan.command
    assert instance.instance_id in plan.workspace


def test_default_roots_cover_supported_launchers(tmp_path: Path) -> None:
    roots = default_instance_roots(home=tmp_path, platform_name="linux")
    launchers = {item.launcher for item in roots}
    assert {
        "Minecraft Launcher",
        "CurseForge",
        "Prism Launcher",
        "MultiMC",
        "Modrinth App",
        "ATLauncher",
        "GDLauncher",
    } <= launchers


def test_invalid_instance_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_instances"):
        discover_modpack_instances((), max_instances=0)
