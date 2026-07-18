from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable, Iterator
from zipfile import BadZipFile, ZipFile

from generator.modpack_scanner import MAX_ARCHIVE_ENTRIES, ModpackProfile, scan_modpack

MAX_CONTENT_JSON_BYTES = 2 * 1024 * 1024
MAX_EMBEDDED_ARCHIVE_BYTES = 512 * 1024 * 1024
_DATA_KINDS = {
    "recipe": ("recipe", "recipes"),
    "advancement": ("advancement", "advancements"),
}
_TAG_ROOTS = ("tag", "tags")
_REGISTRY_ITEM_ROOTS = (
    ("assets", "items"),
    ("assets", "models", "item"),
)


def _humanize(identifier: str) -> str:
    value = identifier.rsplit(":", 1)[-1].rsplit("/", 1)[-1]
    return re.sub(r"[_-]+", " ", value).strip().title() or identifier


def _safe_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.casefold()).strip("_") or "unknown"


def _resource_id(namespace: str, relative: str) -> str:
    return f"{namespace}:{relative.removesuffix('.json')}"


def _is_identifier(value: object) -> bool:
    return isinstance(value, str) and ":" in value and " " not in value


def _read_json(archive: ZipFile, name: str) -> Any:
    info = archive.getinfo(name)
    if info.file_size > MAX_CONTENT_JSON_BYTES:
        raise ValueError(f"content JSON exceeds size limit: {name}")
    return json.loads(archive.read(info).decode("utf-8-sig"))


def _display_text(value: object, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, dict):
        translate = value.get("translate")
        if isinstance(translate, str) and translate.strip():
            return translate.strip()
        text = value.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()
    return fallback


def _item_from_value(value: object) -> str:
    if isinstance(value, str) and _is_identifier(value):
        return value
    if isinstance(value, list):
        for item in value:
            found = _item_from_value(item)
            if found:
                return found
        return ""
    if isinstance(value, dict):
        for key in ("id", "item"):
            candidate = value.get(key)
            if _is_identifier(candidate):
                return str(candidate)
        for key in ("result", "output", "stack"):
            if key in value:
                found = _item_from_value(value[key])
                if found:
                    return found
    return ""


def _result_item(payload: object) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("result", "output", "outputs"):
        if key in payload:
            found = _item_from_value(payload[key])
            if found:
                return found
    return ""


def _collect_ingredient_refs(value: object, *, parent_key: str = "") -> tuple[set[str], set[str]]:
    items: set[str] = set()
    tags: set[str] = set()
    if isinstance(value, list):
        for item in value:
            child_items, child_tags = _collect_ingredient_refs(item, parent_key=parent_key)
            items.update(child_items)
            tags.update(child_tags)
        return items, tags
    if not isinstance(value, dict):
        return items, tags

    for key, child in value.items():
        lowered = str(key).casefold()
        if lowered == "type":
            continue
        if lowered in {"item", "id"} and _is_identifier(child):
            items.add(str(child))
            continue
        if lowered == "tag" and isinstance(child, str) and child.strip():
            tags.add(child.removeprefix("#"))
            continue
        if lowered in {"result", "output", "outputs"} and parent_key == "recipe-root":
            continue
        child_items, child_tags = _collect_ingredient_refs(child, parent_key=lowered)
        items.update(child_items)
        tags.update(child_tags)
    return items, tags


@dataclass(frozen=True, slots=True)
class RecipeRecord:
    recipe_id: str
    recipe_type: str
    result_item: str
    ingredient_items: tuple[str, ...]
    ingredient_tags: tuple[str, ...]
    source_reference: str

    def to_dict(self) -> dict[str, object]:
        return {
            "recipe_id": self.recipe_id,
            "recipe_type": self.recipe_type,
            "result_item": self.result_item,
            "ingredient_items": list(self.ingredient_items),
            "ingredient_tags": list(self.ingredient_tags),
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class AdvancementRecord:
    advancement_id: str
    parent: str
    icon_item: str
    title: str
    description: str
    criteria_count: int
    reward_recipes: tuple[str, ...]
    source_reference: str

    def to_dict(self) -> dict[str, object]:
        return {
            "advancement_id": self.advancement_id,
            "parent": self.parent,
            "icon_item": self.icon_item,
            "title": self.title,
            "description": self.description,
            "criteria_count": self.criteria_count,
            "reward_recipes": list(self.reward_recipes),
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class RegistryRecord:
    identifier: str
    registry_type: str
    source_reference: str

    def to_dict(self) -> dict[str, object]:
        return {
            "identifier": self.identifier,
            "registry_type": self.registry_type,
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class TagRecord:
    tag_id: str
    registry_type: str
    values: tuple[str, ...]
    source_reference: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tag_id": self.tag_id,
            "registry_type": self.registry_type,
            "values": list(self.values),
            "source_reference": self.source_reference,
        }


@dataclass(frozen=True, slots=True)
class QuestCandidate:
    candidate_id: str
    mod_id: str
    title: str
    description: str
    objective_type: str
    objective_id: str
    source_kind: str
    source_id: str
    prerequisite_candidates: tuple[str, ...]
    prerequisite_items: tuple[str, ...]
    prerequisite_tags: tuple[str, ...]
    confidence: float
    score: int

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "mod_id": self.mod_id,
            "title": self.title,
            "description": self.description,
            "objective": {"type": self.objective_type, "id": self.objective_id},
            "source": {"kind": self.source_kind, "id": self.source_id},
            "prerequisite_candidates": list(self.prerequisite_candidates),
            "prerequisite_items": list(self.prerequisite_items),
            "prerequisite_tags": list(self.prerequisite_tags),
            "confidence": self.confidence,
            "score": self.score,
        }


@dataclass(frozen=True, slots=True)
class ModpackContentScan:
    source_path: str
    source_format: str
    pack_name: str
    minecraft_version: str
    loader: str
    recipes: tuple[RecipeRecord, ...]
    advancements: tuple[AdvancementRecord, ...]
    registries: tuple[RegistryRecord, ...]
    tags: tuple[TagRecord, ...]
    candidates: tuple[QuestCandidate, ...]
    candidate_limit: int
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    @property
    def graph_edges(self) -> int:
        return sum(len(item.prerequisite_candidates) for item in self.candidates)

    @property
    def root_candidates(self) -> tuple[str, ...]:
        return tuple(item.candidate_id for item in self.candidates if not item.prerequisite_candidates)

    @property
    def mod_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for candidate in self.candidates:
            counts[candidate.mod_id] = counts.get(candidate.mod_id, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "source": {"path": self.source_path, "format": self.source_format},
            "pack": {
                "name": self.pack_name,
                "minecraft": self.minecraft_version,
                "loader": self.loader,
            },
            "summary": {
                "recipes": len(self.recipes),
                "advancements": len(self.advancements),
                "registry_entries": len(self.registries),
                "tags": len(self.tags),
                "quest_candidates": len(self.candidates),
                "candidate_limit": self.candidate_limit,
                "dependency_edges": self.graph_edges,
                "root_candidates": len(self.root_candidates),
                "candidate_mod_counts": self.mod_counts,
            },
            "recipes": [item.to_dict() for item in self.recipes],
            "advancements": [item.to_dict() for item in self.advancements],
            "registries": [item.to_dict() for item in self.registries],
            "tags": [item.to_dict() for item in self.tags],
            "quest_candidates": [item.to_dict() for item in self.candidates],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Modpack content scan: {'PASS' if self.is_clean else 'FAIL'}",
            f"Source format: {self.source_format}.",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Minecraft: {self.minecraft_version or '<unknown>'}.",
            f"Loader: {self.loader or '<unknown>'}.",
            f"Recipes: {len(self.recipes)}.",
            f"Advancements: {len(self.advancements)}.",
            f"Registry entries: {len(self.registries)}.",
            f"Tags: {len(self.tags)}.",
            f"Quest candidates: {len(self.candidates)}/{self.candidate_limit}.",
            f"Dependency edges: {self.graph_edges}.",
            f"Root candidates: {len(self.root_candidates)}.",
        ]
        lines.extend(f"Candidate mod {name}: {count}." for name, count in self.mod_counts.items())
        lines.extend(f"Warning: {item}" for item in self.warnings)
        lines.extend(f"Error: {item}" for item in self.errors)
        return "\n".join(lines)


@dataclass(slots=True)
class _Collected:
    recipes: list[RecipeRecord]
    advancements: list[AdvancementRecord]
    registries: list[RegistryRecord]
    tags: list[TagRecord]
    translations: dict[str, str]
    warnings: list[str]


def _archive_resource_parts(name: str) -> tuple[str, str, str] | None:
    parts = PurePosixPath(name).parts
    if len(parts) < 4 or parts[0] != "data" or not name.casefold().endswith(".json"):
        return None
    namespace = parts[1]
    root = parts[2].casefold()
    relative = "/".join(parts[3:])
    return namespace, root, relative


def _load_translations(archive: ZipFile, source: str, collected: _Collected) -> None:
    for info in archive.infolist():
        parts = PurePosixPath(info.filename).parts
        if (
            info.is_dir()
            or len(parts) != 4
            or parts[0] != "assets"
            or parts[2] != "lang"
            or parts[3].casefold() != "en_us.json"
        ):
            continue
        try:
            payload = _read_json(archive, info.filename)
        except (KeyError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            collected.warnings.append(f"{source}!{info.filename}: {exc}")
            continue
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(key, str) and isinstance(value, str):
                    collected.translations.setdefault(key, value)


def _localized_name(item_id: str, translations: dict[str, str]) -> str:
    if ":" not in item_id:
        return _humanize(item_id)
    namespace, path = item_id.split(":", 1)
    key_path = path.replace("/", ".")
    for prefix in ("item", "block"):
        key = f"{prefix}.{namespace}.{key_path}"
        if key in translations:
            return translations[key]
    return _humanize(item_id)


def _scan_archive_payload(data: bytes, source: str, collected: _Collected) -> None:
    if len(data) > MAX_EMBEDDED_ARCHIVE_BYTES:
        collected.warnings.append(f"{source}: archive skipped because it exceeds the size limit")
        return
    try:
        archive = ZipFile(BytesIO(data))
    except BadZipFile:
        collected.warnings.append(f"{source}: invalid JAR/ZIP skipped")
        return
    with archive:
        if len(archive.infolist()) > MAX_ARCHIVE_ENTRIES:
            collected.warnings.append(f"{source}: archive contains too many entries")
            return
        _load_translations(archive, source, collected)
        for info in sorted(archive.infolist(), key=lambda value: value.filename.casefold()):
            if info.is_dir() or not info.filename.casefold().endswith(".json"):
                continue
            parts = PurePosixPath(info.filename).parts
            try:
                resource = _archive_resource_parts(info.filename)
                if resource is not None:
                    namespace, root, relative = resource
                    if root in _DATA_KINDS["recipe"]:
                        payload = _read_json(archive, info.filename)
                        if not isinstance(payload, dict):
                            raise ValueError("recipe JSON must be an object")
                        recipe_id = _resource_id(namespace, relative)
                        result = _result_item(payload)
                        items, tags = _collect_ingredient_refs(payload, parent_key="recipe-root")
                        items.discard(result)
                        collected.recipes.append(RecipeRecord(
                            recipe_id=recipe_id,
                            recipe_type=str(payload.get("type", "")),
                            result_item=result,
                            ingredient_items=tuple(sorted(items)),
                            ingredient_tags=tuple(sorted(tags)),
                            source_reference=f"{source}!{info.filename}",
                        ))
                        continue
                    if root in _DATA_KINDS["advancement"]:
                        payload = _read_json(archive, info.filename)
                        if not isinstance(payload, dict):
                            raise ValueError("advancement JSON must be an object")
                        advancement_id = _resource_id(namespace, relative)
                        display = payload.get("display", {})
                        display = display if isinstance(display, dict) else {}
                        icon = _item_from_value(display.get("icon", {}))
                        rewards = payload.get("rewards", {})
                        rewards = rewards if isinstance(rewards, dict) else {}
                        reward_recipes = rewards.get("recipes", [])
                        criteria = payload.get("criteria", {})
                        collected.advancements.append(AdvancementRecord(
                            advancement_id=advancement_id,
                            parent=str(payload.get("parent", "")),
                            icon_item=icon,
                            title=_display_text(display.get("title"), _humanize(advancement_id)),
                            description=_display_text(display.get("description"), ""),
                            criteria_count=len(criteria) if isinstance(criteria, dict) else 0,
                            reward_recipes=tuple(sorted(
                                str(item) for item in reward_recipes if _is_identifier(item)
                            )) if isinstance(reward_recipes, list) else (),
                            source_reference=f"{source}!{info.filename}",
                        ))
                        continue
                    if root in _TAG_ROOTS and len(parts) >= 5:
                        payload = _read_json(archive, info.filename)
                        if not isinstance(payload, dict):
                            raise ValueError("tag JSON must be an object")
                        registry_type = parts[3].casefold().removesuffix("s")
                        tag_relative = "/".join(parts[4:])
                        values = payload.get("values", [])
                        normalized_values = tuple(sorted(
                            str(item.get("id")) if isinstance(item, dict) and _is_identifier(item.get("id")) else str(item)
                            for item in values
                            if _is_identifier(item) or (isinstance(item, dict) and _is_identifier(item.get("id")))
                        )) if isinstance(values, list) else ()
                        collected.tags.append(TagRecord(
                            tag_id=_resource_id(namespace, tag_relative),
                            registry_type=registry_type,
                            values=normalized_values,
                            source_reference=f"{source}!{info.filename}",
                        ))
                        continue

                if len(parts) >= 4 and parts[0] == "assets":
                    namespace = parts[1]
                    if parts[2] == "items":
                        relative = "/".join(parts[3:])
                        collected.registries.append(RegistryRecord(
                            identifier=_resource_id(namespace, relative),
                            registry_type="item",
                            source_reference=f"{source}!{info.filename}",
                        ))
                    elif len(parts) >= 5 and parts[2:4] == ("models", "item"):
                        relative = "/".join(parts[4:])
                        collected.registries.append(RegistryRecord(
                            identifier=_resource_id(namespace, relative),
                            registry_type="item",
                            source_reference=f"{source}!{info.filename}",
                        ))
            except (KeyError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                collected.warnings.append(f"{source}!{info.filename}: {exc}")


def _iter_input_archives(path: Path) -> Iterator[tuple[str, bytes]]:
    if path.is_dir():
        candidates: set[Path] = set()
        if path.name.casefold() == "mods":
            candidates.update(path.glob("*.jar"))
        for relative in (Path("mods"), Path(".minecraft/mods"), Path("overrides/mods")):
            directory = path / relative
            if directory.is_dir():
                candidates.update(directory.glob("*.jar"))
        for archive_path in sorted(candidates, key=lambda value: value.as_posix().casefold()):
            try:
                reference = archive_path.relative_to(path).as_posix() if archive_path.is_relative_to(path) else archive_path.name
                yield reference, archive_path.read_bytes()
            except OSError:
                continue
        # KubeJS and datapack content can exist outside mod JARs. Package it into a
        # temporary in-memory archive-like traversal by scanning JSON files directly.
        return

    try:
        with ZipFile(path) as outer:
            if len(outer.infolist()) > MAX_ARCHIVE_ENTRIES:
                return
            if path.suffix.casefold() == ".jar":
                yield path.name, path.read_bytes()
                return
            for info in sorted(outer.infolist(), key=lambda value: value.filename.casefold()):
                pure = PurePosixPath(info.filename)
                if info.is_dir() or pure.suffix.casefold() != ".jar":
                    continue
                if "mods" not in tuple(part.casefold() for part in pure.parts):
                    continue
                if info.file_size > MAX_EMBEDDED_ARCHIVE_BYTES:
                    continue
                try:
                    yield info.filename, outer.read(info)
                except (KeyError, OSError, RuntimeError):
                    continue
            # Also inspect the outer archive for bundled datapacks/KubeJS resources.
            yield f"{path.name}#outer", path.read_bytes()
    except (BadZipFile, OSError):
        return


def _scan_loose_data(path: Path, collected: _Collected) -> None:
    if not path.is_dir():
        return
    roots = [path / "kubejs" / "data", path / "data"]
    datapacks = path / "datapacks"
    if datapacks.is_dir():
        roots.extend(item / "data" for item in datapacks.iterdir() if item.is_dir())
    for root in roots:
        if not root.is_dir():
            continue
        for file_path in sorted(root.rglob("*.json"), key=lambda value: value.as_posix().casefold()):
            try:
                relative = file_path.relative_to(root)
                parts = relative.parts
                if len(parts) < 3:
                    continue
                namespace, kind = parts[0], parts[1].casefold()
                payload = json.loads(file_path.read_text(encoding="utf-8-sig"))
                reference = file_path.relative_to(path).as_posix()
                resource_relative = "/".join(parts[2:])
                if kind in _DATA_KINDS["recipe"] and isinstance(payload, dict):
                    result = _result_item(payload)
                    items, tags = _collect_ingredient_refs(payload, parent_key="recipe-root")
                    items.discard(result)
                    collected.recipes.append(RecipeRecord(
                        _resource_id(namespace, resource_relative),
                        str(payload.get("type", "")),
                        result,
                        tuple(sorted(items)),
                        tuple(sorted(tags)),
                        reference,
                    ))
                elif kind in _DATA_KINDS["advancement"] and isinstance(payload, dict):
                    display = payload.get("display", {})
                    display = display if isinstance(display, dict) else {}
                    criteria = payload.get("criteria", {})
                    collected.advancements.append(AdvancementRecord(
                        _resource_id(namespace, resource_relative),
                        str(payload.get("parent", "")),
                        _item_from_value(display.get("icon", {})),
                        _display_text(display.get("title"), _humanize(resource_relative)),
                        _display_text(display.get("description"), ""),
                        len(criteria) if isinstance(criteria, dict) else 0,
                        (),
                        reference,
                    ))
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
                collected.warnings.append(f"{file_path.as_posix()}: {exc}")


def _dedupe_records(items: Iterable[Any], key: Any) -> tuple[Any, ...]:
    selected: dict[object, Any] = {}
    for item in items:
        selected.setdefault(key(item), item)
    return tuple(sorted(selected.values(), key=key))


def _candidate_id(kind: str, source_id: str) -> str:
    return f"{kind}__{_safe_identifier(source_id)}"


def _would_cycle(graph: dict[str, set[str]], node: str, dependency: str) -> bool:
    if node == dependency:
        return True
    stack = [dependency]
    visited: set[str] = set()
    while stack:
        current = stack.pop()
        if current == node:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(graph.get(current, ()))
    return False


def _build_candidates(
    profile: ModpackProfile,
    recipes: tuple[RecipeRecord, ...],
    advancements: tuple[AdvancementRecord, ...],
    registries: tuple[RegistryRecord, ...],
    translations: dict[str, str],
    limit: int,
) -> tuple[QuestCandidate, ...]:
    draft: list[dict[str, object]] = []
    output_candidates: dict[str, str] = {}
    advancement_candidates: dict[str, str] = {}

    for advancement in advancements:
        candidate_id = _candidate_id("advancement", advancement.advancement_id)
        advancement_candidates[advancement.advancement_id] = candidate_id
        mod_id = advancement.advancement_id.partition(":")[0]
        title = advancement.title
        if title.startswith(("advancements.", "advancement.")):
            title = _humanize(advancement.advancement_id)
        draft.append({
            "candidate_id": candidate_id,
            "mod_id": mod_id,
            "title": title,
            "description": advancement.description or f"Complete the {title} milestone.",
            "objective_type": "advancement",
            "objective_id": advancement.advancement_id,
            "source_kind": "advancement",
            "source_id": advancement.advancement_id,
            "raw_dependencies": (advancement.parent,) if advancement.parent else (),
            "prerequisite_items": (advancement.icon_item,) if advancement.icon_item else (),
            "prerequisite_tags": (),
            "confidence": 0.98,
            "score": 100 + min(10, advancement.criteria_count),
        })

    # Keep one representative recipe per result item, favoring recipes with more
    # explicit dependencies because they provide stronger progression information.
    recipe_by_output: dict[str, RecipeRecord] = {}
    for recipe in recipes:
        if not recipe.result_item:
            continue
        current = recipe_by_output.get(recipe.result_item)
        if current is None or (
            len(recipe.ingredient_items) + len(recipe.ingredient_tags), recipe.recipe_id
        ) > (
            len(current.ingredient_items) + len(current.ingredient_tags), current.recipe_id
        ):
            recipe_by_output[recipe.result_item] = recipe
    for result_item, recipe in sorted(recipe_by_output.items()):
        candidate_id = _candidate_id("recipe", recipe.recipe_id)
        output_candidates[result_item] = candidate_id
        mod_id = result_item.partition(":")[0]
        item_name = _localized_name(result_item, translations)
        draft.append({
            "candidate_id": candidate_id,
            "mod_id": mod_id,
            "title": f"Craft {item_name}",
            "description": f"Create {item_name} using an available {recipe.recipe_type or 'crafting'} recipe.",
            "objective_type": "item",
            "objective_id": result_item,
            "source_kind": "recipe",
            "source_id": recipe.recipe_id,
            "raw_dependencies": recipe.ingredient_items,
            "prerequisite_items": recipe.ingredient_items,
            "prerequisite_tags": recipe.ingredient_tags,
            "confidence": 0.92,
            "score": 80 + min(15, len(recipe.ingredient_items) * 2 + len(recipe.ingredient_tags)),
        })

    existing_objectives = {
        str(item["objective_id"]) for item in draft if item["objective_type"] == "item"
    }
    for registry in registries:
        if registry.registry_type != "item" or registry.identifier in existing_objectives:
            continue
        mod_id = registry.identifier.partition(":")[0]
        if mod_id == "minecraft":
            continue
        item_name = _localized_name(registry.identifier, translations)
        draft.append({
            "candidate_id": _candidate_id("registry", registry.identifier),
            "mod_id": mod_id,
            "title": f"Obtain {item_name}",
            "description": f"Acquire {item_name} and explore how it fits into the mod's progression.",
            "objective_type": "item",
            "objective_id": registry.identifier,
            "source_kind": "registry",
            "source_id": registry.identifier,
            "raw_dependencies": (),
            "prerequisite_items": (),
            "prerequisite_tags": (),
            "confidence": 0.55,
            "score": 35,
        })

    # Prefer authored advancements, then recipes, then registry fallbacks. Preserve
    # broad mod coverage by using deterministic round-robin selection after scoring.
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in draft:
        grouped.setdefault(str(item["mod_id"]), []).append(item)
    for values in grouped.values():
        values.sort(key=lambda item: (-int(item["score"]), str(item["candidate_id"])))
    selected: list[dict[str, object]] = []
    mod_ids = sorted(grouped)
    while len(selected) < limit and any(grouped.values()):
        for mod_id in mod_ids:
            if grouped[mod_id] and len(selected) < limit:
                selected.append(grouped[mod_id].pop(0))

    selected_ids = {str(item["candidate_id"]) for item in selected}
    graph: dict[str, set[str]] = {identifier: set() for identifier in selected_ids}
    results: list[QuestCandidate] = []
    for item in sorted(selected, key=lambda value: (-int(value["score"]), str(value["candidate_id"]))):
        candidate_id = str(item["candidate_id"])
        dependencies: list[str] = []
        for raw in item["raw_dependencies"]:
            dependency = ""
            raw_value = str(raw)
            if item["source_kind"] == "advancement":
                dependency = advancement_candidates.get(raw_value, "")
            else:
                dependency = output_candidates.get(raw_value, "")
            if dependency and dependency in selected_ids and not _would_cycle(graph, candidate_id, dependency):
                graph[candidate_id].add(dependency)
                dependencies.append(dependency)
        results.append(QuestCandidate(
            candidate_id=candidate_id,
            mod_id=str(item["mod_id"]),
            title=str(item["title"]),
            description=str(item["description"]),
            objective_type=str(item["objective_type"]),
            objective_id=str(item["objective_id"]),
            source_kind=str(item["source_kind"]),
            source_id=str(item["source_id"]),
            prerequisite_candidates=tuple(sorted(set(dependencies))),
            prerequisite_items=tuple(sorted(set(str(value) for value in item["prerequisite_items"]))),
            prerequisite_tags=tuple(sorted(set(str(value) for value in item["prerequisite_tags"]))),
            confidence=float(item["confidence"]),
            score=int(item["score"]),
        ))
    return tuple(sorted(results, key=lambda item: (item.mod_id, -item.score, item.candidate_id)))


def scan_modpack_content(path: Path, *, candidate_limit: int | None = None) -> ModpackContentScan:
    source = path.expanduser()
    profile = scan_modpack(source)
    warnings = list(profile.warnings)
    errors = list(profile.errors)
    collected = _Collected([], [], [], [], {}, warnings)

    if source.exists() and not errors:
        for reference, data in _iter_input_archives(source):
            _scan_archive_payload(data, reference, collected)
        _scan_loose_data(source, collected)

    recipes = _dedupe_records(collected.recipes, lambda item: item.recipe_id)
    advancements = _dedupe_records(collected.advancements, lambda item: item.advancement_id)
    registries = _dedupe_records(collected.registries, lambda item: (item.registry_type, item.identifier))
    tags = _dedupe_records(collected.tags, lambda item: (item.registry_type, item.tag_id))

    default_limit = profile.quest_target.get("maximum", 0)
    if default_limit <= 0:
        default_limit = min(1500, max(25, len(recipes) + len(advancements)))
    limit = candidate_limit if candidate_limit is not None else default_limit
    if limit < 1 or limit > 5000:
        errors.append("candidate limit must be between 1 and 5000")
        limit = min(5000, max(1, limit))

    candidates = _build_candidates(
        profile,
        recipes,
        advancements,
        registries,
        collected.translations,
        limit,
    )
    if not any((recipes, advancements, registries, tags)) and not errors:
        warnings.append("no recipes, advancements, registries, or tags were detected")
    if len(candidates) < min(25, limit) and profile.content_mods:
        warnings.append("content metadata produced fewer quest candidates than the requested target")

    return ModpackContentScan(
        source_path=str(source),
        source_format=profile.source_format,
        pack_name=profile.name,
        minecraft_version=profile.minecraft_version,
        loader=profile.loader,
        recipes=recipes,
        advancements=advancements,
        registries=registries,
        tags=tags,
        candidates=candidates,
        candidate_limit=limit,
        warnings=tuple(sorted(set(warnings))),
        errors=tuple(sorted(set(errors))),
    )
