from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
from typing import Iterable, Mapping

INSTANCE_DISCOVERY_SCHEMA_VERSION = "1.0"
_MAX_METADATA_BYTES = 1_048_576


@dataclass(frozen=True, slots=True)
class InstanceSearchRoot:
    launcher: str
    path: Path


@dataclass(frozen=True, slots=True)
class DiscoveredInstance:
    instance_id: str
    name: str
    launcher: str
    path: str
    game_directory: str
    minecraft_version: str
    loader: str
    loader_version: str
    mod_count: int
    has_ftb_quests: bool
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.instance_id,
            "name": self.name,
            "launcher": self.launcher,
            "path": self.path,
            "game_directory": self.game_directory,
            "minecraft_version": self.minecraft_version,
            "loader": self.loader,
            "loader_version": self.loader_version,
            "mod_count": self.mod_count,
            "has_ftb_quests": self.has_ftb_quests,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class InstanceDiscoveryResult:
    schema_version: str
    searched_roots: tuple[str, ...]
    instances: tuple[DiscoveredInstance, ...]
    inaccessible_roots: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.inaccessible_roots

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "warn",
            "schema_version": self.schema_version,
            "searched_roots": list(self.searched_roots),
            "instance_count": len(self.instances),
            "instances": [item.to_dict() for item in self.instances],
            "inaccessible_roots": list(self.inaccessible_roots),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            "Minecraft instance discovery: " + ("PASS" if self.is_clean else "WARN"),
            f"Search roots: {len(self.searched_roots)}.",
            f"Instances found: {len(self.instances)}.",
        ]
        for instance in self.instances:
            version = instance.minecraft_version or "unknown Minecraft"
            loader = instance.loader or "unknown loader"
            lines.append(
                f"- {instance.name} [{instance.launcher}] · {version} · {loader} · "
                f"{instance.mod_count} mods · {instance.game_directory}"
            )
        lines.extend(f"Inaccessible root: {root}" for root in self.inaccessible_roots)
        return "\n".join(lines)


def _deduplicated_roots(items: Iterable[InstanceSearchRoot]) -> tuple[InstanceSearchRoot, ...]:
    output: list[InstanceSearchRoot] = []
    seen: set[str] = set()
    for item in items:
        key = item.path.expanduser().absolute().as_posix().casefold()
        if key in seen:
            continue
        seen.add(key)
        output.append(InstanceSearchRoot(item.launcher, item.path.expanduser()))
    return tuple(output)


def default_instance_roots(
    *,
    home: Path | None = None,
    platform_name: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> tuple[InstanceSearchRoot, ...]:
    home = Path(home) if home is not None else Path.home()
    system = (platform_name or platform.system()).casefold()
    env = dict(os.environ if environment is None else environment)
    roots: list[InstanceSearchRoot] = []

    if system.startswith("win"):
        appdata = Path(env.get("APPDATA", home / "AppData/Roaming"))
        local = Path(env.get("LOCALAPPDATA", home / "AppData/Local"))
        documents = Path(env.get("USERPROFILE", home)) / "Documents"
        roots.extend(
            (
                InstanceSearchRoot("Minecraft Launcher", appdata / ".minecraft"),
                InstanceSearchRoot(
                    "CurseForge", documents / "Curse/Minecraft/Instances"
                ),
                InstanceSearchRoot(
                    "CurseForge", home / "curseforge/minecraft/Instances"
                ),
                InstanceSearchRoot("Prism Launcher", appdata / "PrismLauncher/instances"),
                InstanceSearchRoot("MultiMC", appdata / "MultiMC/instances"),
                InstanceSearchRoot("Modrinth App", appdata / "com.modrinth.theseus/profiles"),
                InstanceSearchRoot("Modrinth App", local / "ModrinthApp/profiles"),
                InstanceSearchRoot("ATLauncher", appdata / "ATLauncher/instances"),
                InstanceSearchRoot("GDLauncher", appdata / "gdlauncher_next/instances"),
            )
        )
    elif system == "darwin":
        support = home / "Library/Application Support"
        roots.extend(
            (
                InstanceSearchRoot("Minecraft Launcher", support / "minecraft"),
                InstanceSearchRoot("CurseForge", support / "CurseForge/Minecraft/Instances"),
                InstanceSearchRoot("Prism Launcher", support / "PrismLauncher/instances"),
                InstanceSearchRoot("MultiMC", support / "MultiMC/instances"),
                InstanceSearchRoot("Modrinth App", support / "com.modrinth.theseus/profiles"),
                InstanceSearchRoot("ATLauncher", support / "ATLauncher/instances"),
                InstanceSearchRoot("GDLauncher", support / "gdlauncher_next/instances"),
            )
        )
    else:
        roots.extend(
            (
                InstanceSearchRoot("Minecraft Launcher", home / ".minecraft"),
                InstanceSearchRoot("CurseForge", home / "curseforge/minecraft/Instances"),
                InstanceSearchRoot(
                    "Prism Launcher", home / ".local/share/PrismLauncher/instances"
                ),
                InstanceSearchRoot(
                    "Prism Launcher",
                    home
                    / ".var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances",
                ),
                InstanceSearchRoot("MultiMC", home / ".local/share/multimc/instances"),
                InstanceSearchRoot(
                    "Modrinth App", home / ".local/share/modrinth-app/profiles"
                ),
                InstanceSearchRoot(
                    "Modrinth App",
                    home / ".var/app/com.modrinth.ModrinthApp/config/ModrinthApp/profiles",
                ),
                InstanceSearchRoot("ATLauncher", home / ".local/share/ATLauncher/instances"),
                InstanceSearchRoot("ATLauncher", home / ".config/ATLauncher/instances"),
                InstanceSearchRoot("GDLauncher", home / ".local/share/gdlauncher_next/instances"),
            )
        )
    return _deduplicated_roots(roots)


def _safe_json(path: Path) -> dict[str, object]:
    try:
        if not path.is_file() or path.stat().st_size > _MAX_METADATA_BYTES:
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _safe_properties(path: Path) -> dict[str, str]:
    try:
        if not path.is_file() or path.stat().st_size > _MAX_METADATA_BYTES:
            return {}
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")) or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _game_directory(candidate: Path) -> Path:
    for name in (".minecraft", "minecraft"):
        nested = candidate / name
        if nested.is_dir():
            return nested
    return candidate


def _looks_like_instance(candidate: Path) -> bool:
    if not candidate.is_dir():
        return False
    game = _game_directory(candidate)
    return any(
        path.exists()
        for path in (
            candidate / "instance.cfg",
            candidate / "mmc-pack.json",
            candidate / "minecraftinstance.json",
            candidate / "profile.json",
            candidate / "manifest.json",
            candidate / "modrinth.index.json",
            game / "mods",
            game / "config",
        )
    )


def _candidate_directories(root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    if _looks_like_instance(root):
        candidates.append(root)
    try:
        children = sorted(
            (child for child in root.iterdir() if child.is_dir()),
            key=lambda item: item.name.casefold(),
        )
    except OSError:
        return tuple(candidates)
    candidates.extend(child for child in children if _looks_like_instance(child))
    return tuple(candidates)


def _loader_from_text(value: str) -> tuple[str, str]:
    lowered = value.casefold()
    for loader in ("neoforge", "forge", "fabric", "quilt"):
        if loader in lowered:
            version = value
            for separator in ("-", ":", " "):
                prefix = loader + separator
                index = lowered.find(prefix)
                if index >= 0:
                    version = value[index + len(prefix) :]
                    break
            return loader, version.strip()
    return "", ""


def _metadata(candidate: Path, launcher_hint: str) -> dict[str, str]:
    game = _game_directory(candidate)
    name = candidate.name
    launcher = launcher_hint
    minecraft_version = ""
    loader = ""
    loader_version = ""
    evidence: list[str] = []

    curse = _safe_json(candidate / "minecraftinstance.json")
    if curse:
        launcher = "CurseForge"
        name = str(curse.get("name") or curse.get("displayName") or name)
        minecraft_version = str(
            curse.get("gameVersion") or curse.get("minecraftVersion") or ""
        )
        base_loader = curse.get("baseModLoader")
        if isinstance(base_loader, dict):
            loader, loader_version = _loader_from_text(str(base_loader.get("name", "")))
        elif base_loader:
            loader, loader_version = _loader_from_text(str(base_loader))
        evidence.append("minecraftinstance.json")

    manifest = _safe_json(candidate / "manifest.json")
    if manifest:
        launcher = "CurseForge"
        name = str(manifest.get("name") or name)
        minecraft = manifest.get("minecraft")
        if isinstance(minecraft, dict):
            minecraft_version = str(minecraft.get("version") or minecraft_version)
            loaders = minecraft.get("modLoaders")
            if isinstance(loaders, list):
                for item in loaders:
                    if isinstance(item, dict):
                        loader, loader_version = _loader_from_text(str(item.get("id", "")))
                        if loader:
                            break
        evidence.append("manifest.json")

    profile = _safe_json(candidate / "profile.json")
    if profile:
        launcher = "Modrinth App"
        name = str(profile.get("name") or profile.get("display_name") or name)
        minecraft_version = str(
            profile.get("game_version")
            or profile.get("minecraft_version")
            or profile.get("gameVersion")
            or minecraft_version
        )
        profile_loader = str(profile.get("loader") or profile.get("mod_loader") or "")
        found_loader, found_version = _loader_from_text(profile_loader)
        loader = found_loader or profile_loader.casefold()
        loader_version = str(profile.get("loader_version") or found_version)
        evidence.append("profile.json")

    cfg = _safe_properties(candidate / "instance.cfg")
    if cfg:
        launcher = launcher_hint or "Prism Launcher"
        name = cfg.get("name", name)
        evidence.append("instance.cfg")

    mmc = _safe_json(candidate / "mmc-pack.json")
    if mmc:
        launcher = launcher_hint or "Prism Launcher"
        components = mmc.get("components")
        if isinstance(components, list):
            for component in components:
                if not isinstance(component, dict):
                    continue
                uid = str(component.get("uid", ""))
                version = str(component.get("version", ""))
                if uid == "net.minecraft":
                    minecraft_version = version or minecraft_version
                found_loader, found_version = _loader_from_text(uid)
                if found_loader:
                    loader = found_loader
                    loader_version = version or found_version
        evidence.append("mmc-pack.json")

    if game != candidate:
        evidence.append(game.name)
    if (game / "mods").is_dir():
        evidence.append("mods")
    if (game / "config").is_dir():
        evidence.append("config")
    return {
        "name": name,
        "launcher": launcher,
        "minecraft_version": minecraft_version,
        "loader": loader,
        "loader_version": loader_version,
        "evidence": "\0".join(dict.fromkeys(evidence)),
    }


def _inspect(candidate: Path, launcher_hint: str) -> DiscoveredInstance | None:
    if not _looks_like_instance(candidate):
        return None
    try:
        canonical_candidate = candidate.resolve()
        game = _game_directory(candidate).resolve()
    except OSError:
        return None
    metadata = _metadata(candidate, launcher_hint)
    mods = game / "mods"
    try:
        mod_count = sum(
            1
            for item in mods.iterdir()
            if item.is_file() and item.suffix.casefold() in {".jar", ".zip"}
        ) if mods.is_dir() else 0
    except OSError:
        mod_count = 0
    identity = f"{metadata['launcher']}\0{game.as_posix()}".encode("utf-8")
    return DiscoveredInstance(
        instance_id="instance-" + hashlib.sha256(identity).hexdigest()[:16],
        name=metadata["name"] or candidate.name,
        launcher=metadata["launcher"] or launcher_hint or "Unknown launcher",
        path=canonical_candidate.as_posix(),
        game_directory=game.as_posix(),
        minecraft_version=metadata["minecraft_version"],
        loader=metadata["loader"],
        loader_version=metadata["loader_version"],
        mod_count=mod_count,
        has_ftb_quests=(game / "config/ftbquests").is_dir(),
        evidence=tuple(item for item in metadata["evidence"].split("\0") if item),
    )


def discover_modpack_instances(
    search_roots: Iterable[InstanceSearchRoot | tuple[str, Path] | Path] | None = None,
    *,
    home: Path | None = None,
    platform_name: str | None = None,
    environment: Mapping[str, str] | None = None,
    max_instances: int = 500,
) -> InstanceDiscoveryResult:
    if max_instances <= 0:
        raise ValueError("max_instances must be positive")
    if search_roots is None:
        roots = default_instance_roots(
            home=home,
            platform_name=platform_name,
            environment=environment,
        )
    else:
        normalized: list[InstanceSearchRoot] = []
        for item in search_roots:
            if isinstance(item, InstanceSearchRoot):
                normalized.append(item)
            elif isinstance(item, tuple):
                launcher, path = item
                normalized.append(InstanceSearchRoot(str(launcher), Path(path)))
            else:
                normalized.append(InstanceSearchRoot("Custom", Path(item)))
        roots = _deduplicated_roots(normalized)

    found: list[DiscoveredInstance] = []
    inaccessible: list[str] = []
    seen_games: set[str] = set()
    searched: list[str] = []
    for root in roots:
        path = root.path.expanduser()
        searched.append(path.as_posix())
        if not path.exists():
            continue
        if not path.is_dir() or not os.access(path, os.R_OK):
            inaccessible.append(path.as_posix())
            continue
        for candidate in _candidate_directories(path):
            instance = _inspect(candidate, root.launcher)
            if instance is None:
                continue
            key = instance.game_directory.casefold()
            if key in seen_games:
                continue
            seen_games.add(key)
            found.append(instance)
            if len(found) >= max_instances:
                break
        if len(found) >= max_instances:
            break

    found.sort(
        key=lambda item: (
            item.name.casefold(),
            item.launcher.casefold(),
            item.game_directory.casefold(),
        )
    )
    return InstanceDiscoveryResult(
        schema_version=INSTANCE_DISCOVERY_SCHEMA_VERSION,
        searched_roots=tuple(searched),
        instances=tuple(found),
        inaccessible_roots=tuple(sorted(set(inaccessible))),
    )
