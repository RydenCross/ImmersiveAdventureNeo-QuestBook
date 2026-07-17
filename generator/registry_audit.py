from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile, ZipFile

from model import Project, RewardType, TaskType


@dataclass(frozen=True, slots=True)
class RegistryReference:
    kind: str
    item_id: str
    chapter: str
    quest: str


@dataclass(frozen=True, slots=True)
class RegistryAudit:
    references: tuple[RegistryReference, ...]
    known_items: frozenset[str]
    covered_namespaces: frozenset[str]
    missing: tuple[RegistryReference, ...]
    unverifiable: tuple[RegistryReference, ...]
    sources: tuple[Path, ...]

    @property
    def verified(self) -> tuple[RegistryReference, ...]:
        return tuple(
            reference
            for reference in self.references
            if reference.item_id in self.known_items
        )

    @property
    def is_clean(self) -> bool:
        return not self.missing

    def format(self) -> str:
        kind_counts = Counter(reference.kind for reference in self.references)
        lines = [
            f"Registry audit: {len(self.references)} reference(s) from "
            f"{sum(kind_counts.values()) and len(kind_counts)} type(s).",
            f"Loaded {len(self.known_items)} item id(s) across "
            f"{len(self.covered_namespaces)} namespace(s) from {len(self.sources)} source(s).",
            f"Verified: {len(self.verified)}.",
            f"Missing: {len(self.missing)}.",
            f"Unverifiable namespaces: {len(self.unverifiable)} reference(s).",
        ]
        if kind_counts:
            lines.append(
                "References: " + ", ".join(f"{kind}={count}" for kind, count in sorted(kind_counts.items())) + "."
            )
        if self.covered_namespaces:
            lines.append("Covered namespaces: " + ", ".join(sorted(self.covered_namespaces)) + ".")
        for reference in self.missing:
            lines.append(
                f"MISSING {reference.kind}: {reference.item_id} "
                f"({reference.chapter} / {reference.quest})"
            )
        return "\n".join(lines)


def audit_registry(project: Project, sources: Iterable[Path]) -> RegistryAudit:
    normalized_sources = tuple(Path(source) for source in sources)
    known_items: set[str] = set()
    covered_namespaces: set[str] = set()

    for source in normalized_sources:
        source_items, source_namespaces = load_registry_source(source)
        known_items.update(source_items)
        covered_namespaces.update(source_namespaces)

    references = tuple(iter_registry_references(project))
    missing = tuple(
        reference
        for reference in references
        if namespace(reference.item_id) in covered_namespaces
        and reference.item_id not in known_items
    )
    unverifiable = tuple(
        reference
        for reference in references
        if namespace(reference.item_id) not in covered_namespaces
    )
    return RegistryAudit(
        references=references,
        known_items=frozenset(known_items),
        covered_namespaces=frozenset(covered_namespaces),
        missing=missing,
        unverifiable=unverifiable,
        sources=normalized_sources,
    )


def iter_registry_references(project: Project) -> Iterable[RegistryReference]:
    for chapter in project.chapters:
        yield RegistryReference("chapter_icon", chapter.icon, chapter.title, chapter.title)
        for quest in chapter.quests:
            yield RegistryReference("quest_icon", quest.icon, chapter.title, quest.title)
            for task in quest.tasks:
                if task.type is TaskType.ITEM:
                    item_id = nested_item_id(task.data)
                    if item_id:
                        yield RegistryReference("item_task", item_id, chapter.title, quest.title)
            for reward in quest.rewards:
                if reward.type is RewardType.ITEM:
                    item_id = nested_item_id(reward.data)
                    if item_id:
                        yield RegistryReference("item_reward", item_id, chapter.title, quest.title)


def nested_item_id(data: dict[str, object]) -> str | None:
    item = data.get("item")
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        value = item.get("id")
        return value if isinstance(value, str) else None
    return None


def namespace(item_id: str) -> str:
    return item_id.partition(":")[0]


def load_registry_source(path: Path) -> tuple[set[str], set[str]]:
    if path.is_dir():
        items: set[str] = set()
        namespaces: set[str] = set()
        for child in sorted(path.iterdir()):
            if child.suffix.lower() in {".jar", ".zip", ".json"}:
                child_items, child_namespaces = load_registry_source(child)
                items.update(child_items)
                namespaces.update(child_namespaces)
        return items, namespaces
    if path.suffix.lower() in {".jar", ".zip"}:
        return load_archive(path)
    if path.suffix.lower() == ".json":
        return load_json(path)
    raise ValueError(f"Unsupported registry source: {path}")


def load_archive(path: Path) -> tuple[set[str], set[str]]:
    items: set[str] = set()
    namespaces: set[str] = set()
    try:
        with ZipFile(path) as archive:
            for name in archive.namelist():
                parts = name.split("/")
                if len(parts) < 4 or parts[0] != "assets":
                    continue
                namespace_id = parts[1]
                relative = "/".join(parts[3:])
                if parts[2] == "items" and relative.endswith(".json"):
                    items.add(f"{namespace_id}:{relative[:-5]}")
                    namespaces.add(namespace_id)
                elif parts[2:4] == ["models", "item"] and relative.endswith(".json"):
                    # Here relative starts with the item path because models/item was consumed.
                    item_path = "/".join(parts[4:])[:-5]
                    if item_path:
                        items.add(f"{namespace_id}:{item_path}")
                        namespaces.add(namespace_id)
    except BadZipFile as exc:
        raise ValueError(f"Invalid JAR/ZIP registry source: {path}") from exc
    return items, namespaces


def load_json(path: Path) -> tuple[set[str], set[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON registry source: {path}") from exc

    items = set(extract_item_ids(data))
    explicit_namespaces: set[str] = set()
    if isinstance(data, dict):
        value = data.get("namespaces")
        if isinstance(value, list):
            explicit_namespaces.update(item for item in value if isinstance(item, str))
    namespaces = {namespace(item_id) for item_id in items} | explicit_namespaces
    return items, namespaces


def extract_item_ids(value: object) -> Iterable[str]:
    if isinstance(value, str):
        if ":" in value and " " not in value:
            yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from extract_item_ids(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and ":" in key and " " not in key:
                yield key
            yield from extract_item_ids(item)
