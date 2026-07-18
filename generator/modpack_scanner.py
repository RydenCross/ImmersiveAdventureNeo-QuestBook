from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import tomllib
from typing import Any, Iterable
from zipfile import BadZipFile, ZipFile

MAX_ARCHIVE_ENTRIES = 100_000
MAX_METADATA_BYTES = 4 * 1024 * 1024
_METADATA_NAMES = (
    "META-INF/neoforge.mods.toml",
    "META-INF/mods.toml",
    "fabric.mod.json",
    "quilt.mod.json",
    "mcmod.info",
    "META-INF/MANIFEST.MF",
)

_LIBRARY_TOKENS = (
    "api",
    "library",
    "lib",
    "core",
    "config",
    "architectury",
    "cloth",
    "kotlin",
    "resourceful",
    "bookshelf",
    "framework",
    "moonlight",
    "geckolib",
    "balm",
    "curios",
)
_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("technology", ("create", "mekanism", "thermal", "industrial", "engineering", "tech", "power", "energy", "factory", "machine")),
    ("magic", ("ars", "magic", "botania", "occult", "hex", "spell", "mana", "sorcery", "apotheosis")),
    ("storage", ("storage", "ae2", "appliedenergistics", "refined", "drawer", "chest", "backpack")),
    ("exploration", ("aether", "twilight", "dimension", "dungeon", "biome", "explor", "adventure", "structure")),
    ("farming", ("farm", "crop", "food", "cooking", "agriculture", "harvest", "bees", "botany")),
    ("combat", ("combat", "weapon", "armor", "boss", "mobs", "arsenal")),
    ("utility", ("utility", "quality", "map", "inventory", "hud", "tooltip", "recipe", "jei", "emi")),
)
_CATEGORY_WEIGHTS = {
    "technology": 28,
    "magic": 24,
    "storage": 18,
    "exploration": 16,
    "farming": 14,
    "combat": 12,
    "utility": 6,
    "unknown": 8,
    "library": 0,
}
_MAJOR_MOD_TOKENS = (
    "mekanism",
    "create",
    "appliedenergistics",
    "ae2",
    "thermal",
    "botania",
    "arsnouveau",
    "industrialforegoing",
    "immersiveengineering",
    "twilightforest",
)


@dataclass(frozen=True, slots=True)
class PackMod:
    mod_id: str
    display_name: str
    version: str
    source: str
    source_reference: str
    category: str
    library: bool
    resolved: bool
    quest_weight: int

    def to_dict(self) -> dict[str, object]:
        return {
            "mod_id": self.mod_id,
            "display_name": self.display_name,
            "version": self.version,
            "source": self.source,
            "source_reference": self.source_reference,
            "category": self.category,
            "library": self.library,
            "resolved": self.resolved,
            "quest_weight": self.quest_weight,
        }


@dataclass(frozen=True, slots=True)
class ModpackProfile:
    source_path: str
    source_format: str
    name: str
    version: str
    minecraft_version: str
    loader: str
    loader_version: str
    mods: tuple[PackMod, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    @property
    def content_mods(self) -> tuple[PackMod, ...]:
        return tuple(mod for mod in self.mods if not mod.library)

    @property
    def library_mods(self) -> tuple[PackMod, ...]:
        return tuple(mod for mod in self.mods if mod.library)

    @property
    def unresolved_mods(self) -> tuple[PackMod, ...]:
        return tuple(mod for mod in self.mods if not mod.resolved)

    @property
    def category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for mod in self.mods:
            counts[mod.category] = counts.get(mod.category, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def quest_target(self) -> dict[str, int]:
        weighted = sum(mod.quest_weight for mod in self.content_mods)
        target = max(25, min(1200, weighted)) if self.content_mods else 0
        minimum = max(10, round(target * 0.8)) if target else 0
        maximum = min(1500, max(target, round(target * 1.2))) if target else 0
        return {"minimum": minimum, "target": target, "maximum": maximum}

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "source": {
                "path": self.source_path,
                "format": self.source_format,
            },
            "pack": {
                "name": self.name,
                "version": self.version,
                "minecraft": self.minecraft_version,
                "loader": self.loader,
                "loader_version": self.loader_version,
            },
            "summary": {
                "mods": len(self.mods),
                "content_mods": len(self.content_mods),
                "library_mods": len(self.library_mods),
                "resolved_mods": len(self.mods) - len(self.unresolved_mods),
                "unresolved_mods": len(self.unresolved_mods),
                "category_counts": self.category_counts,
                "recommended_quests": self.quest_target,
            },
            "mods": [mod.to_dict() for mod in self.mods],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        target = self.quest_target
        lines = [
            f"Modpack scan: {'PASS' if self.is_clean else 'FAIL'}",
            f"Source format: {self.source_format}.",
            f"Pack: {self.name or '<unknown>'} {self.version or ''}".rstrip() + ".",
            f"Minecraft: {self.minecraft_version or '<unknown>'}.",
            f"Loader: {self.loader or '<unknown>'} {self.loader_version or ''}".rstrip() + ".",
            f"Mods: {len(self.mods)} ({len(self.content_mods)} content, {len(self.library_mods)} libraries).",
            f"Resolved mod IDs: {len(self.mods) - len(self.unresolved_mods)}.",
            f"Unresolved mod references: {len(self.unresolved_mods)}.",
            f"Recommended quests: {target['minimum']}-{target['maximum']} (target {target['target']}).",
        ]
        lines.extend(f"Category {name}: {count}." for name, count in self.category_counts.items())
        lines.extend(f"Warning: {warning}" for warning in self.warnings)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def _safe_json(data: bytes) -> Any:
    if len(data) > MAX_METADATA_BYTES:
        raise ValueError("metadata file exceeds the size limit")
    return json.loads(data.decode("utf-8-sig"))


def _safe_toml(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_METADATA_BYTES:
        raise ValueError("metadata file exceeds the size limit")
    payload = tomllib.loads(data.decode("utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("TOML metadata must be an object")
    return payload


def _slug(value: str, fallback: str = "unknown") -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", value.casefold()).strip("_")
    return normalized or fallback


def _filename_mod_id(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[-_](?:mc)?\d+(?:\.\d+)*(?:[-+._][a-z0-9]+)*$", "", stem, flags=re.I)
    return _slug(stem)


def _classification(mod_id: str, display_name: str) -> tuple[str, bool, int]:
    combined = f"{mod_id} {display_name}".casefold().replace(" ", "")
    library = any(token in combined for token in _LIBRARY_TOKENS)
    if library:
        return "library", True, 0
    category = "unknown"
    for name, tokens in _CATEGORY_KEYWORDS:
        if any(token.replace(" ", "") in combined for token in tokens):
            category = name
            break
    weight = _CATEGORY_WEIGHTS[category]
    if any(token in combined for token in _MAJOR_MOD_TOKENS):
        weight = max(weight, 42)
    return category, False, weight


def _pack_mod(
    *,
    mod_id: str,
    display_name: str,
    version: str,
    source: str,
    source_reference: str,
    resolved: bool,
) -> PackMod:
    category, library, quest_weight = _classification(mod_id, display_name)
    return PackMod(
        mod_id=_slug(mod_id),
        display_name=display_name.strip() or mod_id,
        version=version.strip(),
        source=source,
        source_reference=source_reference,
        category=category,
        library=library,
        resolved=resolved,
        quest_weight=quest_weight,
    )


def _manifest_fields(data: bytes) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in data.decode("utf-8", errors="replace").splitlines():
        if ":" in raw_line:
            key, value = raw_line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def inspect_mod_jar(data: bytes, reference: str) -> tuple[PackMod, ...]:
    try:
        archive = ZipFile(BytesIO(data))
    except BadZipFile:
        return ()
    with archive:
        if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES:
            return ()
        names = set(archive.namelist())
        manifest = _manifest_fields(archive.read("META-INF/MANIFEST.MF")) if "META-INF/MANIFEST.MF" in names else {}
        fallback_version = manifest.get("Implementation-Version", "")
        for metadata_name in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml"):
            if metadata_name not in names:
                continue
            try:
                payload = _safe_toml(archive.read(metadata_name))
            except (KeyError, UnicodeError, ValueError, tomllib.TOMLDecodeError):
                continue
            mods = payload.get("mods", [])
            if isinstance(mods, dict):
                mods = [mods]
            results: list[PackMod] = []
            if isinstance(mods, list):
                for raw in mods:
                    if not isinstance(raw, dict):
                        continue
                    mod_id = str(raw.get("modId", "")).strip()
                    if not mod_id:
                        continue
                    version = str(raw.get("version", "")).strip()
                    if version.startswith("${"):
                        version = fallback_version
                    results.append(_pack_mod(
                        mod_id=mod_id,
                        display_name=str(raw.get("displayName", mod_id)),
                        version=version or fallback_version,
                        source="jar-metadata",
                        source_reference=reference,
                        resolved=True,
                    ))
            if results:
                return tuple(results)

        if "fabric.mod.json" in names:
            try:
                payload = _safe_json(archive.read("fabric.mod.json"))
            except (KeyError, UnicodeError, ValueError, json.JSONDecodeError):
                payload = None
            if isinstance(payload, dict) and payload.get("id"):
                mod_id = str(payload["id"])
                return (_pack_mod(
                    mod_id=mod_id,
                    display_name=str(payload.get("name", mod_id)),
                    version=str(payload.get("version", fallback_version)),
                    source="jar-metadata",
                    source_reference=reference,
                    resolved=True,
                ),)

        if "quilt.mod.json" in names:
            try:
                payload = _safe_json(archive.read("quilt.mod.json"))
            except (KeyError, UnicodeError, ValueError, json.JSONDecodeError):
                payload = None
            loader = payload.get("quilt_loader", {}) if isinstance(payload, dict) else {}
            metadata = loader.get("metadata", {}) if isinstance(loader, dict) else {}
            if isinstance(loader, dict) and loader.get("id"):
                mod_id = str(loader["id"])
                return (_pack_mod(
                    mod_id=mod_id,
                    display_name=str(metadata.get("name", mod_id)) if isinstance(metadata, dict) else mod_id,
                    version=str(loader.get("version", fallback_version)),
                    source="jar-metadata",
                    source_reference=reference,
                    resolved=True,
                ),)

        if "mcmod.info" in names:
            try:
                payload = _safe_json(archive.read("mcmod.info"))
            except (KeyError, UnicodeError, ValueError, json.JSONDecodeError):
                payload = None
            entries = payload if isinstance(payload, list) else [payload] if isinstance(payload, dict) else []
            results = []
            for raw in entries:
                if not isinstance(raw, dict) or not raw.get("modid"):
                    continue
                mod_id = str(raw["modid"])
                results.append(_pack_mod(
                    mod_id=mod_id,
                    display_name=str(raw.get("name", mod_id)),
                    version=str(raw.get("version", fallback_version)),
                    source="jar-metadata",
                    source_reference=reference,
                    resolved=True,
                ))
            if results:
                return tuple(results)

        title = manifest.get("Implementation-Title") or manifest.get("Specification-Title")
        if title:
            mod_id = _filename_mod_id(reference)
            return (_pack_mod(
                mod_id=mod_id,
                display_name=title,
                version=fallback_version,
                source="jar-manifest",
                source_reference=reference,
                resolved=False,
            ),)
    return ()


def _loader_from_modrinth(dependencies: dict[str, Any]) -> tuple[str, str, str]:
    minecraft = str(dependencies.get("minecraft", ""))
    for key, display in (
        ("neoforge", "NeoForge"),
        ("forge", "Forge"),
        ("fabric-loader", "Fabric"),
        ("quilt-loader", "Quilt"),
    ):
        if key in dependencies:
            return minecraft, display, str(dependencies[key])
    return minecraft, "", ""


def _read_archive_member(archive: ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.file_size > MAX_METADATA_BYTES and not name.casefold().endswith(".jar"):
        raise ValueError(f"metadata file too large: {name}")
    return archive.read(info)


def _mods_from_archive(archive: ZipFile) -> list[PackMod]:
    mods: list[PackMod] = []
    for info in sorted(archive.infolist(), key=lambda item: item.filename.casefold()):
        pure = PurePosixPath(info.filename)
        if info.is_dir() or pure.suffix.casefold() != ".jar":
            continue
        parts = tuple(part.casefold() for part in pure.parts)
        if "mods" not in parts and len(pure.parts) > 1:
            continue
        try:
            data = archive.read(info)
        except (KeyError, OSError, RuntimeError):
            continue
        inspected = inspect_mod_jar(data, info.filename)
        if inspected:
            mods.extend(inspected)
        else:
            mod_id = _filename_mod_id(pure.name)
            mods.append(_pack_mod(
                mod_id=mod_id,
                display_name=Path(pure.name).stem,
                version="",
                source="embedded-jar",
                source_reference=info.filename,
                resolved=False,
            ))
    return mods


def _mods_from_directory(path: Path) -> list[PackMod]:
    candidates: set[Path] = set()
    if path.name.casefold() == "mods":
        candidates.update(path.glob("*.jar"))
    for relative in (Path("mods"), Path(".minecraft/mods")):
        directory = path / relative
        if directory.is_dir():
            candidates.update(directory.glob("*.jar"))
    mods: list[PackMod] = []
    for jar in sorted(candidates, key=lambda item: item.as_posix().casefold()):
        try:
            data = jar.read_bytes()
        except OSError:
            continue
        reference = jar.relative_to(path).as_posix() if jar.is_relative_to(path) else jar.name
        inspected = inspect_mod_jar(data, reference)
        if inspected:
            mods.extend(inspected)
        else:
            mod_id = _filename_mod_id(jar.name)
            mods.append(_pack_mod(
                mod_id=mod_id,
                display_name=jar.stem,
                version="",
                source="local-jar",
                source_reference=reference,
                resolved=False,
            ))
    return mods


def _deduplicate(mods: Iterable[PackMod]) -> tuple[PackMod, ...]:
    selected: dict[tuple[str, str], PackMod] = {}
    for mod in mods:
        key = (mod.mod_id, mod.version)
        current = selected.get(key)
        if current is None or (mod.resolved and not current.resolved):
            selected[key] = mod
    return tuple(sorted(selected.values(), key=lambda mod: (mod.display_name.casefold(), mod.mod_id, mod.version)))


def _scan_modrinth(payload: dict[str, Any], embedded: Iterable[PackMod]) -> tuple[str, str, str, str, list[PackMod], list[str], str]:
    dependencies = payload.get("dependencies", {})
    dependencies = dependencies if isinstance(dependencies, dict) else {}
    minecraft, loader, loader_version = _loader_from_modrinth(dependencies)
    mods = list(embedded)
    warnings: list[str] = []
    files = payload.get("files", [])
    if not isinstance(files, list):
        files = []
        warnings.append("modrinth files list is invalid")
    embedded_refs = {mod.source_reference.casefold() for mod in mods}
    for raw in files:
        if not isinstance(raw, dict):
            continue
        path = str(raw.get("path", "")).strip()
        if not path.casefold().endswith(".jar") or path.casefold() in embedded_refs:
            continue
        mod_id = _filename_mod_id(PurePosixPath(path).name)
        mods.append(_pack_mod(
            mod_id=mod_id,
            display_name=Path(PurePosixPath(path).name).stem,
            version="",
            source="modrinth-index",
            source_reference=path,
            resolved=False,
        ))
    return (
        str(payload.get("name", "")),
        str(payload.get("versionId", "")),
        minecraft,
        loader,
        mods,
        warnings + (["loader version was not declared"] if loader and not loader_version else []),
    ) + (loader_version,)


def _scan_curseforge(payload: dict[str, Any], embedded: Iterable[PackMod]) -> tuple[str, str, str, str, list[PackMod], list[str], str]:
    minecraft = payload.get("minecraft", {})
    minecraft = minecraft if isinstance(minecraft, dict) else {}
    mod_loaders = minecraft.get("modLoaders", [])
    mod_loaders = mod_loaders if isinstance(mod_loaders, list) else []
    loader = ""
    loader_version = ""
    for raw in mod_loaders:
        if not isinstance(raw, dict):
            continue
        loader_id = str(raw.get("id", ""))
        lowered = loader_id.casefold()
        if lowered.startswith("neoforge-"):
            loader, loader_version = "NeoForge", loader_id.split("-", 1)[1]
            break
        if lowered.startswith("forge-"):
            loader, loader_version = "Forge", loader_id.split("-", 1)[1]
            break
        if lowered.startswith("fabric-"):
            loader, loader_version = "Fabric", loader_id.split("-", 1)[1]
            break
    mods = list(embedded)
    warnings: list[str] = []
    files = payload.get("files", [])
    if not isinstance(files, list):
        files = []
        warnings.append("CurseForge files list is invalid")
    for raw in files:
        if not isinstance(raw, dict):
            continue
        project_id = str(raw.get("projectID", "")).strip()
        file_id = str(raw.get("fileID", "")).strip()
        if not project_id:
            continue
        reference = f"curseforge:{project_id}:{file_id}"
        mods.append(_pack_mod(
            mod_id=f"curseforge_{project_id}",
            display_name=f"CurseForge project {project_id}",
            version=file_id,
            source="curseforge-manifest",
            source_reference=reference,
            resolved=False,
        ))
    return (
        str(payload.get("name", "")),
        str(payload.get("version", "")),
        str(minecraft.get("version", "")),
        loader,
        mods,
        warnings,
        loader_version,
    )


def _prism_platform(payload: dict[str, Any]) -> tuple[str, str, str]:
    components = payload.get("components", [])
    components = components if isinstance(components, list) else []
    minecraft = ""
    loader = ""
    loader_version = ""
    for component in components:
        if not isinstance(component, dict):
            continue
        uid = str(component.get("uid", "")).casefold()
        version = str(component.get("version", ""))
        if uid == "net.minecraft":
            minecraft = version
        elif "neoforge" in uid:
            loader, loader_version = "NeoForge", version
        elif uid.endswith("forge"):
            loader, loader_version = "Forge", version
        elif "fabric-loader" in uid:
            loader, loader_version = "Fabric", version
        elif "quilt-loader" in uid:
            loader, loader_version = "Quilt", version
    return minecraft, loader, loader_version


def scan_modpack(path: Path) -> ModpackProfile:
    source = path.expanduser()
    if not source.exists():
        return ModpackProfile(str(source), "missing", "", "", "", "", "", (), (), ("input path does not exist",))

    warnings: list[str] = []
    errors: list[str] = []
    name = source.stem
    version = ""
    minecraft = ""
    loader = ""
    loader_version = ""
    source_format = "mods-directory" if source.is_dir() and source.name.casefold() == "mods" else "instance-directory"
    mods: list[PackMod] = []

    if source.is_dir():
        mods = _mods_from_directory(source)
        modrinth_path = source / "modrinth.index.json"
        curseforge_path = source / "manifest.json"
        prism_path = source / "mmc-pack.json"
        try:
            if modrinth_path.is_file():
                payload = json.loads(modrinth_path.read_text(encoding="utf-8-sig"))
                if not isinstance(payload, dict):
                    raise ValueError("modrinth.index.json must be an object")
                name, version, minecraft, loader, mods, extra_warnings, loader_version = _scan_modrinth(payload, mods)
                warnings.extend(extra_warnings)
                source_format = "modrinth-directory"
            elif curseforge_path.is_file():
                payload = json.loads(curseforge_path.read_text(encoding="utf-8-sig"))
                if not isinstance(payload, dict):
                    raise ValueError("manifest.json must be an object")
                name, version, minecraft, loader, mods, extra_warnings, loader_version = _scan_curseforge(payload, mods)
                warnings.extend(extra_warnings)
                source_format = "curseforge-directory"
            elif prism_path.is_file():
                payload = json.loads(prism_path.read_text(encoding="utf-8-sig"))
                if isinstance(payload, dict):
                    minecraft, loader, loader_version = _prism_platform(payload)
                source_format = "prism-instance"
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    else:
        try:
            with ZipFile(source) as archive:
                if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES:
                    raise ValueError("archive contains too many entries")
                names = set(archive.namelist())
                mods = _mods_from_archive(archive)
                if "modrinth.index.json" in names:
                    payload = _safe_json(_read_archive_member(archive, "modrinth.index.json"))
                    if not isinstance(payload, dict):
                        raise ValueError("modrinth.index.json must be an object")
                    name, version, minecraft, loader, mods, extra_warnings, loader_version = _scan_modrinth(payload, mods)
                    warnings.extend(extra_warnings)
                    source_format = "modrinth-mrpack"
                elif "manifest.json" in names:
                    payload = _safe_json(_read_archive_member(archive, "manifest.json"))
                    if not isinstance(payload, dict):
                        raise ValueError("manifest.json must be an object")
                    name, version, minecraft, loader, mods, extra_warnings, loader_version = _scan_curseforge(payload, mods)
                    warnings.extend(extra_warnings)
                    source_format = "curseforge-zip"
                elif "mmc-pack.json" in names:
                    payload = _safe_json(_read_archive_member(archive, "mmc-pack.json"))
                    if isinstance(payload, dict):
                        minecraft, loader, loader_version = _prism_platform(payload)
                    source_format = "prism-archive"
                elif source.suffix.casefold() == ".jar":
                    source_format = "single-mod-jar"
                else:
                    source_format = "server-or-instance-zip"
        except (BadZipFile, KeyError, OSError, RuntimeError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"unable to inspect archive: {exc}")
            source_format = "invalid-archive"

    deduplicated = _deduplicate(mods)
    if not deduplicated and not errors:
        warnings.append("no mod entries were detected")
    if any(not mod.resolved for mod in deduplicated):
        warnings.append("some mod IDs were inferred from filenames or remote manifest references")
    return ModpackProfile(
        source_path=str(source),
        source_format=source_format,
        name=name,
        version=version,
        minecraft_version=minecraft,
        loader=loader,
        loader_version=loader_version,
        mods=deduplicated,
        warnings=tuple(sorted(set(warnings))),
        errors=tuple(sorted(set(errors))),
    )
