from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

DEFAULT_POLICY_PATH = Path("config/mod-compatibility.json")
DEFAULT_CONTENT_DIRECTORY = Path("content")
_ALLOWED_REQUIREMENTS = frozenset({"required", "optional"})
_ALLOWED_STATUSES = frozenset({"supported", "experimental", "deprecated", "unsupported"})


@dataclass(frozen=True, slots=True)
class ModCompatibilityContract:
    minecraft_versions: tuple[str, ...]
    loader: str
    loader_version: str
    quest_format: str
    declared_mods: int
    supported_mods: tuple[str, ...]
    experimental_mods: tuple[str, ...]
    deprecated_mods: tuple[str, ...]
    unsupported_mods: tuple[str, ...]
    missing_content_modules: tuple[str, ...]
    unknown_content_modules: tuple[str, ...]
    duplicate_mod_ids: tuple[str, ...]
    duplicate_content_modules: tuple[str, ...]
    invalid_entries: tuple[str, ...]
    invalid_incompatibilities: tuple[str, ...]
    matrix: tuple[dict[str, str], ...]

    @property
    def is_clean(self) -> bool:
        return not any((
            self.missing_content_modules,
            self.unknown_content_modules,
            self.duplicate_mod_ids,
            self.duplicate_content_modules,
            self.invalid_entries,
            self.invalid_incompatibilities,
            self.unsupported_mods,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "platform": {
                "minecraft": list(self.minecraft_versions),
                "loader": self.loader,
                "loader_version": self.loader_version,
                "quest_format": self.quest_format,
            },
            "declared_mods": self.declared_mods,
            "supported_mods": list(self.supported_mods),
            "experimental_mods": list(self.experimental_mods),
            "deprecated_mods": list(self.deprecated_mods),
            "unsupported_mods": list(self.unsupported_mods),
            "missing_content_modules": list(self.missing_content_modules),
            "unknown_content_modules": list(self.unknown_content_modules),
            "duplicate_mod_ids": list(self.duplicate_mod_ids),
            "duplicate_content_modules": list(self.duplicate_content_modules),
            "invalid_entries": list(self.invalid_entries),
            "invalid_incompatibilities": list(self.invalid_incompatibilities),
            "matrix": list(self.matrix),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Mod compatibility contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Minecraft versions: {', '.join(self.minecraft_versions) or 'none'}.",
            f"Loader: {self.loader} {self.loader_version}.",
            f"Quest format: {self.quest_format}.",
            f"Declared mods: {self.declared_mods}.",
            f"Supported mods: {len(self.supported_mods)}.",
            f"Experimental mods: {len(self.experimental_mods)}.",
            f"Deprecated mods: {len(self.deprecated_mods)}.",
            f"Unsupported mods: {len(self.unsupported_mods)}.",
            f"Missing content modules: {len(self.missing_content_modules)}.",
            f"Unknown content modules: {len(self.unknown_content_modules)}.",
            f"Invalid entries: {len(self.invalid_entries)}.",
            f"Invalid incompatibilities: {len(self.invalid_incompatibilities)}.",
        ]
        lines.extend(f"Missing module: {value}" for value in self.missing_content_modules)
        lines.extend(f"Unknown module: {value}" for value in self.unknown_content_modules)
        lines.extend(f"Invalid entry: {value}" for value in self.invalid_entries)
        lines.extend(f"Invalid incompatibility: {value}" for value in self.invalid_incompatibilities)
        return "\n".join(lines)


def _duplicates(values: list[str]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def _content_modules(directory: Path) -> set[str]:
    if not directory.is_dir():
        return set()
    return {
        path.name
        for path in directory.iterdir()
        if path.is_dir() and not path.name.startswith("__") and any(path.glob("*.py"))
    }


def run_mod_compatibility_contract(
    policy_path: Path = DEFAULT_POLICY_PATH,
    content_directory: Path = DEFAULT_CONTENT_DIRECTORY,
) -> ModCompatibilityContract:
    payload: Any = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("compatibility policy must be a JSON object")
    platform = payload.get("platform", {})
    mods = payload.get("mods", [])
    incompatibilities = payload.get("incompatibilities", [])
    if not isinstance(platform, dict) or not isinstance(mods, list) or not isinstance(incompatibilities, list):
        raise ValueError("platform, mods, and incompatibilities must use their documented JSON types")

    minecraft = tuple(str(value).strip() for value in platform.get("minecraft", []) if str(value).strip())
    loader = str(platform.get("loader", "")).strip()
    loader_version = str(platform.get("loader_version", "")).strip()
    quest_format = str(platform.get("quest_format", "")).strip()
    invalid: list[str] = []
    if not minecraft:
        invalid.append("platform.minecraft")
    if loader != "NeoForge":
        invalid.append("platform.loader")
    if not loader_version:
        invalid.append("platform.loader_version")
    if not quest_format:
        invalid.append("platform.quest_format")

    rows: list[dict[str, str]] = []
    mod_ids: list[str] = []
    modules: list[str] = []
    statuses: dict[str, list[str]] = {name: [] for name in _ALLOWED_STATUSES}
    for index, raw in enumerate(mods):
        if not isinstance(raw, dict):
            invalid.append(f"mods[{index}]")
            continue
        row = {key: str(raw.get(key, "")).strip() for key in (
            "content_module", "mod_id", "display_name", "requirement", "version_policy", "status"
        )}
        if not row["content_module"] or not row["mod_id"] or not row["display_name"] or not row["version_policy"]:
            invalid.append(f"mods[{index}].required_fields")
        if row["requirement"] not in _ALLOWED_REQUIREMENTS:
            invalid.append(f"mods[{index}].requirement")
        if row["status"] not in _ALLOWED_STATUSES:
            invalid.append(f"mods[{index}].status")
        else:
            statuses[row["status"]].append(row["mod_id"])
        modules.append(row["content_module"])
        mod_ids.append(row["mod_id"])
        rows.append(row)

    known_ids = set(mod_ids)
    invalid_pairs: list[str] = []
    seen_pairs: set[tuple[str, str]] = set()
    for index, raw in enumerate(incompatibilities):
        if not isinstance(raw, list) or len(raw) != 2:
            invalid_pairs.append(f"incompatibilities[{index}]")
            continue
        left, right = sorted((str(raw[0]).strip(), str(raw[1]).strip()))
        pair = (left, right)
        if not left or left == right or left not in known_ids or right not in known_ids or pair in seen_pairs:
            invalid_pairs.append(f"{left}:{right}")
        seen_pairs.add(pair)

    authored = _content_modules(content_directory)
    declared = set(modules)
    return ModCompatibilityContract(
        minecraft_versions=minecraft,
        loader=loader,
        loader_version=loader_version,
        quest_format=quest_format,
        declared_mods=len(rows),
        supported_mods=tuple(sorted(statuses["supported"])),
        experimental_mods=tuple(sorted(statuses["experimental"])),
        deprecated_mods=tuple(sorted(statuses["deprecated"])),
        unsupported_mods=tuple(sorted(statuses["unsupported"])),
        missing_content_modules=tuple(sorted(authored - declared)),
        unknown_content_modules=tuple(sorted(declared - authored)),
        duplicate_mod_ids=_duplicates(mod_ids),
        duplicate_content_modules=_duplicates(modules),
        invalid_entries=tuple(sorted(invalid)),
        invalid_incompatibilities=tuple(sorted(invalid_pairs)),
        matrix=tuple(sorted(rows, key=lambda row: row["display_name"].casefold())),
    )
