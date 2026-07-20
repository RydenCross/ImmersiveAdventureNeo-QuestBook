from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.desktop_launcher import build_editor_launch_plan
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_ui import EDITOR_HTML
from generator.instance_discovery import discover_modpack_instances


@dataclass(frozen=True, slots=True)
class DesktopLauncherContract:
    common_launchers_discovered: bool
    metadata_detected: bool
    deterministic_discovery: bool
    duplicate_instances_removed: bool
    safe_editor_command: bool
    instance_api_route: bool
    browser_instance_selection: bool
    empty_directories_ignored: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.common_launchers_discovered,
                self.metadata_detected,
                self.deterministic_discovery,
                self.duplicate_instances_removed,
                self.safe_editor_command,
                self.instance_api_route,
                self.browser_instance_selection,
                self.empty_directories_ignored,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "common_launchers_discovered": self.common_launchers_discovered,
            "metadata_detected": self.metadata_detected,
            "deterministic_discovery": self.deterministic_discovery,
            "duplicate_instances_removed": self.duplicate_instances_removed,
            "safe_editor_command": self.safe_editor_command,
            "instance_api_route": self.instance_api_route,
            "browser_instance_selection": self.browser_instance_selection,
            "empty_directories_ignored": self.empty_directories_ignored,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                "Desktop launcher and instance discovery contract: "
                + ("PASS" if self.is_clean else "FAIL"),
                "Common launchers discovered: "
                f"{'yes' if self.common_launchers_discovered else 'no'}.",
                f"Metadata detected: {'yes' if self.metadata_detected else 'no'}.",
                f"Deterministic discovery: {'yes' if self.deterministic_discovery else 'no'}.",
                "Duplicate instances removed: "
                f"{'yes' if self.duplicate_instances_removed else 'no'}.",
                f"Safe editor command: {'yes' if self.safe_editor_command else 'no'}.",
                f"Instance API route: {'yes' if self.instance_api_route else 'no'}.",
                "Browser instance selection: "
                f"{'yes' if self.browser_instance_selection else 'no'}.",
                f"Empty directories ignored: {'yes' if self.empty_directories_ignored else 'no'}.",
            )
        )


def _write_jar(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PK\x03\x04contract")


def run_desktop_launcher_contract() -> DesktopLauncherContract:
    with TemporaryDirectory(prefix="desktop-launcher-contract-") as temporary:
        home = Path(temporary) / "home"
        _write_jar(home / ".minecraft/mods/base.jar")

        curse = home / "curseforge/minecraft/Instances/Technology"
        _write_jar(curse / "mods/technology.jar")
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
        _write_jar(prism / ".minecraft/mods/magic.jar")
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
        _write_jar(modrinth / "mods/storage.jar")
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

        first = discover_modpack_instances(home=home, platform_name="linux")
        second = discover_modpack_instances(home=home, platform_name="linux")
        names = {item.name for item in first.instances}
        technology = next(item for item in first.instances if item.name == "Technology Pack")
        plan = build_editor_launch_plan(
            technology,
            workspace_root=Path(temporary) / "workspace",
            open_browser=False,
            python_executable="python-contract",
        )

        session = EditorSession.empty(workspace=Path(temporary) / "editor")
        api = handle_editor_api(session, "GET", "/api/v1/instances")
        empty = Path(temporary) / "empty"
        empty.mkdir()
        ignored = discover_modpack_instances((empty,)).instances == ()

        return DesktopLauncherContract(
            common_launchers_discovered={
                ".minecraft",
                "Technology Pack",
                "Magic Pack",
                "Storage Pack",
            }
            <= names,
            metadata_detected=(
                technology.minecraft_version == "1.21.1"
                and technology.loader == "neoforge"
                and technology.loader_version == "21.1.80"
            ),
            deterministic_discovery=first.format_json() == second.format_json(),
            duplicate_instances_removed=(
                len({item.game_directory.casefold() for item in first.instances})
                == len(first.instances)
            ),
            safe_editor_command=(
                plan.command[:4]
                == ("python-contract", "-m", "generator", "quest-editor-serve")
                and technology.game_directory in plan.command
                and "--no-browser" in plan.command
                and technology.instance_id in plan.workspace
            ),
            instance_api_route=(
                api.status_code == 200
                and isinstance(api.payload.get("instances"), list)
                and "instance_count" in api.payload
            ),
            browser_instance_selection=all(
                token in EDITOR_HTML
                for token in (
                    "/instances",
                    "Choose the discovered instance number",
                    "game_directory",
                )
            ),
            empty_directories_ignored=ignored,
        )
