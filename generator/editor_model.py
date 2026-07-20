from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Mapping

from generator.progression_planner import (
    BlueprintChapter,
    BlueprintObjective,
    BlueprintQuest,
    BlueprintReward,
    QuestBlueprint,
)
from generator.quest_description_generator import generate_quest_description_plan
from generator.reward_planner import REWARD_POLICIES, generate_quest_reward_plan

EDITOR_SCHEMA_VERSION = "1.0"
EDITOR_REWARD_DECISIONS = ("unassigned", "none", "rewarded")
EDITOR_OPERATION_TYPES = ("update_chapter", "update_quest", "move_quest", "set_dependency")


@dataclass(frozen=True, slots=True)
class EditorObjective:
    objective_type: str
    identifier: str
    count: int = 1

    def to_dict(self) -> dict[str, object]:
        return {"type": self.objective_type, "id": self.identifier, "count": self.count}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorObjective:
        return cls(
            objective_type=str(payload.get("type", "")),
            identifier=str(payload.get("id", "")),
            count=int(payload.get("count", 1)),
        )


@dataclass(frozen=True, slots=True)
class EditorReward:
    reward_type: str
    identifier: str
    count: int = 1
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.reward_type,
            "id": self.identifier,
            "count": self.count,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorReward:
        return cls(
            reward_type=str(payload.get("type", "")),
            identifier=str(payload.get("id", "")),
            count=int(payload.get("count", 1)),
            reason=str(payload.get("reason", "")),
        )


@dataclass(frozen=True, slots=True)
class EditorChapter:
    chapter_id: str
    title: str
    category: str
    mod_id: str
    order: int
    prerequisite_chapters: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.chapter_id,
            "title": self.title,
            "category": self.category,
            "mod_id": self.mod_id,
            "order": self.order,
            "prerequisite_chapters": list(self.prerequisite_chapters),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorChapter:
        prerequisites = payload.get("prerequisite_chapters", ())
        return cls(
            chapter_id=str(payload.get("id", "")),
            title=str(payload.get("title", "")),
            category=str(payload.get("category", "unknown")),
            mod_id=str(payload.get("mod_id", "unknown")),
            order=int(payload.get("order", 0)),
            prerequisite_chapters=tuple(str(item) for item in prerequisites or ()),
        )


@dataclass(frozen=True, slots=True)
class EditorQuest:
    quest_id: str
    chapter_id: str
    candidate_id: str
    order: int
    title: str
    description: str
    objective: EditorObjective
    prerequisite_items: tuple[str, ...]
    prerequisite_tags: tuple[str, ...]
    source_kind: str
    source_id: str
    confidence: float
    score: int
    x: int
    y: int
    review_required: bool
    reward_decision: str = "unassigned"
    rewards: tuple[EditorReward, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.quest_id,
            "chapter_id": self.chapter_id,
            "candidate_id": self.candidate_id,
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "objective": self.objective.to_dict(),
            "prerequisite_items": list(self.prerequisite_items),
            "prerequisite_tags": list(self.prerequisite_tags),
            "source": {"kind": self.source_kind, "id": self.source_id},
            "confidence": self.confidence,
            "score": self.score,
            "position": {"x": self.x, "y": self.y},
            "review_required": self.review_required,
            "reward_decision": self.reward_decision,
            "rewards": [reward.to_dict() for reward in self.rewards],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorQuest:
        objective = payload.get("objective", {})
        source = payload.get("source", {})
        position = payload.get("position", {})
        rewards = payload.get("rewards", ())
        return cls(
            quest_id=str(payload.get("id", "")),
            chapter_id=str(payload.get("chapter_id", "")),
            candidate_id=str(payload.get("candidate_id", payload.get("id", ""))),
            order=int(payload.get("order", 0)),
            title=str(payload.get("title", "")),
            description=str(payload.get("description", "")),
            objective=EditorObjective.from_dict(
                objective if isinstance(objective, Mapping) else {}
            ),
            prerequisite_items=tuple(
                str(item) for item in payload.get("prerequisite_items", ()) or ()
            ),
            prerequisite_tags=tuple(
                str(item) for item in payload.get("prerequisite_tags", ()) or ()
            ),
            source_kind=str(source.get("kind", "") if isinstance(source, Mapping) else ""),
            source_id=str(source.get("id", "") if isinstance(source, Mapping) else ""),
            confidence=float(payload.get("confidence", 0.0)),
            score=int(payload.get("score", 0)),
            x=int(position.get("x", 0) if isinstance(position, Mapping) else 0),
            y=int(position.get("y", 0) if isinstance(position, Mapping) else 0),
            review_required=bool(payload.get("review_required", False)),
            reward_decision=str(payload.get("reward_decision", "unassigned")),
            rewards=tuple(
                EditorReward.from_dict(item)
                for item in rewards or ()
                if isinstance(item, Mapping)
            ),
        )


@dataclass(frozen=True, slots=True)
class EditorEdge:
    edge_id: str
    prerequisite_quest: str
    dependent_quest: str

    @classmethod
    def create(cls, prerequisite_quest: str, dependent_quest: str) -> EditorEdge:
        return cls(
            edge_id=f"dependency:{prerequisite_quest}->{dependent_quest}",
            prerequisite_quest=prerequisite_quest,
            dependent_quest=dependent_quest,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.edge_id,
            "type": "prerequisite",
            "from": self.prerequisite_quest,
            "to": self.dependent_quest,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorEdge:
        prerequisite = str(payload.get("from", ""))
        dependent = str(payload.get("to", ""))
        return cls(
            edge_id=str(payload.get("id", f"dependency:{prerequisite}->{dependent}")),
            prerequisite_quest=prerequisite,
            dependent_quest=dependent,
        )


@dataclass(frozen=True, slots=True)
class EditorChange:
    revision: int
    action: str
    target_id: str
    changed_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "revision": self.revision,
            "action": self.action,
            "target_id": self.target_id,
            "changed_fields": list(self.changed_fields),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorChange:
        return cls(
            revision=int(payload.get("revision", 0)),
            action=str(payload.get("action", "")),
            target_id=str(payload.get("target_id", "")),
            changed_fields=tuple(str(item) for item in payload.get("changed_fields", ()) or ()),
        )


@dataclass(frozen=True, slots=True)
class EditorValidation:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class EditorDocument:
    schema_version: str
    revision: int
    source_path: str
    source_format: str
    pack_name: str
    minecraft_version: str
    loader: str
    requested_quests: int
    available_candidates: int
    chapters: tuple[EditorChapter, ...]
    quests: tuple[EditorQuest, ...]
    edges: tuple[EditorEdge, ...]
    dirty_entities: tuple[str, ...] = ()
    change_log: tuple[EditorChange, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def quest_count(self) -> int:
        return len(self.quests)

    @property
    def is_clean(self) -> bool:
        return not self.errors and validate_editor_document(self).is_clean

    def to_dict(self) -> dict[str, object]:
        validation = validate_editor_document(self)
        return {
            "status": "pass" if not self.errors and validation.is_clean else "fail",
            "schema_version": self.schema_version,
            "revision": self.revision,
            "source": {"path": self.source_path, "format": self.source_format},
            "pack": {
                "name": self.pack_name,
                "minecraft": self.minecraft_version,
                "loader": self.loader,
            },
            "summary": {
                "chapters": len(self.chapters),
                "quests": len(self.quests),
                "dependency_edges": len(self.edges),
                "requested_quests": self.requested_quests,
                "available_candidates": self.available_candidates,
                "dirty_entities": len(self.dirty_entities),
                "changes": len(self.change_log),
            },
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "quests": [quest.to_dict() for quest in self.quests],
            "edges": [edge.to_dict() for edge in self.edges],
            "dirty_entities": list(self.dirty_entities),
            "change_log": [change.to_dict() for change in self.change_log],
            "validation": validation.to_dict(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        validation = validate_editor_document(self)
        return "\n".join((
            f"Quest editor model: {'PASS' if not self.errors and validation.is_clean else 'FAIL'}",
            f"Schema version: {self.schema_version}.",
            f"Revision: {self.revision}.",
            f"Pack: {self.pack_name or '<unknown>'}.",
            f"Chapters: {len(self.chapters)}.",
            f"Quests: {len(self.quests)}.",
            f"Dependency edges: {len(self.edges)}.",
            f"Dirty entities: {len(self.dirty_entities)}.",
            f"Recorded changes: {len(self.change_log)}.",
            f"Validation errors: {len(validation.errors) + len(self.errors)}.",
            f"Validation warnings: {len(validation.warnings) + len(self.warnings)}.",
        ))

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> EditorDocument:
        source = payload.get("source", {})
        pack = payload.get("pack", {})
        summary = payload.get("summary", {})
        chapters = payload.get("chapters", ())
        quests = payload.get("quests", ())
        edges = payload.get("edges", ())
        changes = payload.get("change_log", ())
        return cls(
            schema_version=str(payload.get("schema_version", "")),
            revision=int(payload.get("revision", 0)),
            source_path=str(source.get("path", "") if isinstance(source, Mapping) else ""),
            source_format=str(source.get("format", "") if isinstance(source, Mapping) else ""),
            pack_name=str(pack.get("name", "") if isinstance(pack, Mapping) else ""),
            minecraft_version=str(pack.get("minecraft", "") if isinstance(pack, Mapping) else ""),
            loader=str(pack.get("loader", "") if isinstance(pack, Mapping) else ""),
            requested_quests=int(
                summary.get("requested_quests", 0) if isinstance(summary, Mapping) else 0
            ),
            available_candidates=int(
                summary.get("available_candidates", 0) if isinstance(summary, Mapping) else 0
            ),
            chapters=tuple(
                EditorChapter.from_dict(item)
                for item in chapters or ()
                if isinstance(item, Mapping)
            ),
            quests=tuple(
                EditorQuest.from_dict(item)
                for item in quests or ()
                if isinstance(item, Mapping)
            ),
            edges=tuple(
                EditorEdge.from_dict(item)
                for item in edges or ()
                if isinstance(item, Mapping)
            ),
            dirty_entities=tuple(str(item) for item in payload.get("dirty_entities", ()) or ()),
            change_log=tuple(
                EditorChange.from_dict(item)
                for item in changes or ()
                if isinstance(item, Mapping)
            ),
            warnings=tuple(str(item) for item in payload.get("warnings", ()) or ()),
            errors=tuple(str(item) for item in payload.get("errors", ()) or ()),
        )


@dataclass(frozen=True, slots=True)
class EditorOperation:
    action: str
    target_id: str
    values: tuple[tuple[str, object], ...] = ()

    @classmethod
    def create(cls, action: str, target_id: str, **values: object) -> EditorOperation:
        return cls(action=action, target_id=target_id, values=tuple(sorted(values.items())))

    def value_map(self) -> dict[str, object]:
        return dict(self.values)

    def to_dict(self) -> dict[str, object]:
        return {"action": self.action, "target_id": self.target_id, "values": self.value_map()}


@dataclass(frozen=True, slots=True)
class EditorTransaction:
    before: EditorDocument
    after: EditorDocument
    operation: EditorOperation
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors and self.after.revision == self.before.revision + 1

    def undo(self) -> EditorDocument:
        return self.before

    def redo(self) -> EditorDocument:
        return self.after


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def _cycle_nodes(quest_ids: set[str], edges: tuple[EditorEdge, ...]) -> tuple[str, ...]:
    incoming = {identifier: 0 for identifier in quest_ids}
    outgoing: dict[str, set[str]] = {identifier: set() for identifier in quest_ids}
    for edge in edges:
        if edge.prerequisite_quest in quest_ids and edge.dependent_quest in quest_ids:
            if edge.dependent_quest not in outgoing[edge.prerequisite_quest]:
                outgoing[edge.prerequisite_quest].add(edge.dependent_quest)
                incoming[edge.dependent_quest] += 1
    ready = sorted(identifier for identifier, count in incoming.items() if count == 0)
    visited: set[str] = set()
    while ready:
        identifier = ready.pop(0)
        visited.add(identifier)
        for dependent in sorted(outgoing[identifier]):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                ready.append(dependent)
                ready.sort()
    return tuple(sorted(quest_ids - visited))


def validate_editor_document(document: EditorDocument) -> EditorValidation:
    errors: list[str] = []
    warnings: list[str] = []
    if document.schema_version != EDITOR_SCHEMA_VERSION:
        errors.append(
            f"unsupported editor schema version {document.schema_version!r}; "
            f"expected {EDITOR_SCHEMA_VERSION!r}"
        )
    chapter_ids = tuple(chapter.chapter_id for chapter in document.chapters)
    quest_ids = tuple(quest.quest_id for quest in document.quests)
    edge_ids = tuple(edge.edge_id for edge in document.edges)
    for label, values in (("chapter", chapter_ids), ("quest", quest_ids), ("edge", edge_ids)):
        errors.extend(f"duplicate {label} id: {value}" for value in _duplicates(values))

    chapter_set = set(chapter_ids)
    quest_set = set(quest_ids)
    duplicate_orders = _duplicates(tuple(str(chapter.order) for chapter in document.chapters))
    errors.extend(f"duplicate chapter order: {value}" for value in duplicate_orders)

    for chapter in document.chapters:
        if not chapter.chapter_id:
            errors.append("chapter id must not be empty")
        if not chapter.title.strip():
            errors.append(f"chapter {chapter.chapter_id!r} has an empty title")
        unknown = sorted(set(chapter.prerequisite_chapters) - chapter_set)
        errors.extend(
            f"chapter {chapter.chapter_id!r} references unknown prerequisite chapter {value!r}"
            for value in unknown
        )

    positions: dict[tuple[str, int, int], list[str]] = {}
    quest_orders: dict[str, list[str]] = {}
    for quest in document.quests:
        quest_orders.setdefault(quest.chapter_id, []).append(str(quest.order))
        if quest.chapter_id not in chapter_set:
            errors.append(
                f"quest {quest.quest_id!r} references unknown chapter {quest.chapter_id!r}"
            )
        if not quest.title.strip():
            errors.append(f"quest {quest.quest_id!r} has an empty title")
        if quest.objective.objective_type not in {"item", "advancement"}:
            errors.append(
                f"quest {quest.quest_id!r} uses unsupported objective type "
                f"{quest.objective.objective_type!r}"
            )
        if not quest.objective.identifier:
            errors.append(f"quest {quest.quest_id!r} has an empty objective identifier")
        if quest.objective.count < 1:
            errors.append(f"quest {quest.quest_id!r} has a non-positive objective count")
        if quest.reward_decision not in EDITOR_REWARD_DECISIONS:
            errors.append(
                f"quest {quest.quest_id!r} has invalid reward decision {quest.reward_decision!r}"
            )
        if quest.reward_decision == "rewarded" and not quest.rewards:
            errors.append(f"quest {quest.quest_id!r} is rewarded but has no reward records")
        if quest.reward_decision != "rewarded" and quest.rewards:
            errors.append(
                f"quest {quest.quest_id!r} contains rewards without a rewarded decision"
            )
        for reward in quest.rewards:
            if not reward.identifier or reward.count < 1:
                errors.append(f"quest {quest.quest_id!r} contains an invalid reward")
        positions.setdefault((quest.chapter_id, quest.x, quest.y), []).append(quest.quest_id)

    for chapter_id, orders in sorted(quest_orders.items()):
        errors.extend(
            f"duplicate quest order in chapter {chapter_id!r}: {value}"
            for value in _duplicates(tuple(orders))
        )

    warnings.extend(
        "layout collision in chapter "
        f"{chapter_id!r} at ({x}, {y}): {', '.join(sorted(identifiers))}"
        for (chapter_id, x, y), identifiers in sorted(positions.items())
        if len(identifiers) > 1
    )

    relations: list[tuple[str, str]] = []
    for edge in document.edges:
        if edge.prerequisite_quest not in quest_set:
            errors.append(
                f"edge {edge.edge_id!r} references unknown prerequisite quest "
                f"{edge.prerequisite_quest!r}"
            )
        if edge.dependent_quest not in quest_set:
            errors.append(
                f"edge {edge.edge_id!r} references unknown dependent quest "
                f"{edge.dependent_quest!r}"
            )
        if edge.prerequisite_quest == edge.dependent_quest:
            errors.append(f"edge {edge.edge_id!r} is self-referential")
        relations.append((edge.prerequisite_quest, edge.dependent_quest))
    for relation in sorted({item for item in relations if relations.count(item) > 1}):
        errors.append(f"duplicate dependency edge: {relation[0]} -> {relation[1]}")
    cycle_nodes = _cycle_nodes(quest_set, document.edges)
    if cycle_nodes:
        errors.append(f"dependency cycle involves: {', '.join(cycle_nodes)}")

    if document.revision < 0:
        errors.append("document revision must not be negative")
    if document.change_log and document.change_log[-1].revision != document.revision:
        errors.append("latest change-log revision does not match document revision")
    return EditorValidation(tuple(sorted(set(errors))), tuple(sorted(set(warnings))))


def build_editor_document(blueprint: QuestBlueprint) -> EditorDocument:
    chapters = tuple(
        EditorChapter(
            chapter_id=chapter.chapter_id,
            title=chapter.title,
            category=chapter.category,
            mod_id=chapter.mod_id,
            order=chapter.order,
            prerequisite_chapters=chapter.prerequisite_chapters,
        )
        for chapter in sorted(blueprint.chapters, key=lambda item: (item.order, item.chapter_id))
    )
    quests = tuple(
        EditorQuest(
            quest_id=quest.quest_id,
            chapter_id=chapter.chapter_id,
            candidate_id=quest.candidate_id,
            order=quest_index,
            title=quest.title,
            description=quest.description,
            objective=EditorObjective(
                quest.objective.objective_type,
                quest.objective.identifier,
                quest.objective.count,
            ),
            prerequisite_items=quest.prerequisite_items,
            prerequisite_tags=quest.prerequisite_tags,
            source_kind=quest.source_kind,
            source_id=quest.source_id,
            confidence=quest.confidence,
            score=quest.score,
            x=quest.x,
            y=quest.y,
            review_required=quest.review_required,
            reward_decision=quest.reward_decision,
            rewards=tuple(
                EditorReward(
                    reward.reward_type,
                    reward.identifier,
                    reward.count,
                    reward.reason,
                )
                for reward in quest.rewards
            ),
        )
        for chapter in sorted(blueprint.chapters, key=lambda item: (item.order, item.chapter_id))
        for quest_index, quest in enumerate(chapter.quests)
    )
    edges = tuple(sorted(
        (
            EditorEdge.create(prerequisite, quest.quest_id)
            for chapter in blueprint.chapters
            for quest in chapter.quests
            for prerequisite in quest.prerequisite_quests
        ),
        key=lambda item: (item.prerequisite_quest, item.dependent_quest),
    ))
    return EditorDocument(
        schema_version=EDITOR_SCHEMA_VERSION,
        revision=0,
        source_path=blueprint.source_path,
        source_format=blueprint.source_format,
        pack_name=blueprint.pack_name,
        minecraft_version=blueprint.minecraft_version,
        loader=blueprint.loader,
        requested_quests=blueprint.requested_quests,
        available_candidates=blueprint.available_candidates,
        chapters=chapters,
        quests=quests,
        edges=edges,
        warnings=blueprint.warnings,
        errors=blueprint.errors,
    )


def editor_document_to_blueprint(document: EditorDocument) -> QuestBlueprint:
    incoming: dict[str, list[str]] = {quest.quest_id: [] for quest in document.quests}
    for edge in document.edges:
        if edge.dependent_quest in incoming:
            incoming[edge.dependent_quest].append(edge.prerequisite_quest)
    quests_by_chapter: dict[str, list[BlueprintQuest]] = {
        chapter.chapter_id: [] for chapter in document.chapters
    }
    for quest in document.quests:
        quests_by_chapter.setdefault(quest.chapter_id, []).append(BlueprintQuest(
            quest_id=quest.quest_id,
            candidate_id=quest.candidate_id,
            title=quest.title,
            description=quest.description,
            objective=BlueprintObjective(
                quest.objective.objective_type,
                quest.objective.identifier,
                quest.objective.count,
            ),
            prerequisite_quests=tuple(sorted(incoming.get(quest.quest_id, ()))),
            prerequisite_items=quest.prerequisite_items,
            prerequisite_tags=quest.prerequisite_tags,
            source_kind=quest.source_kind,
            source_id=quest.source_id,
            confidence=quest.confidence,
            score=quest.score,
            x=quest.x,
            y=quest.y,
            review_required=quest.review_required,
            reward_decision=quest.reward_decision,
            rewards=tuple(
                BlueprintReward(
                    reward.reward_type,
                    reward.identifier,
                    reward.count,
                    reward.reason,
                )
                for reward in quest.rewards
            ),
        ))
    chapters = tuple(
        BlueprintChapter(
            chapter_id=chapter.chapter_id,
            title=chapter.title,
            category=chapter.category,
            mod_id=chapter.mod_id,
            order=chapter.order,
            prerequisite_chapters=chapter.prerequisite_chapters,
            quests=tuple(sorted(
                quests_by_chapter.get(chapter.chapter_id, ()),
                key=lambda item: (
                    next(
                        (
                            quest.order
                            for quest in document.quests
                            if quest.quest_id == item.quest_id
                        ),
                        0,
                    ),
                    item.quest_id,
                ),
            )),
        )
        for chapter in sorted(document.chapters, key=lambda item: (item.order, item.chapter_id))
    )
    return QuestBlueprint(
        source_path=document.source_path,
        source_format=document.source_format,
        pack_name=document.pack_name,
        minecraft_version=document.minecraft_version,
        loader=document.loader,
        requested_quests=document.requested_quests,
        available_candidates=document.available_candidates,
        chapters=chapters,
        warnings=document.warnings,
        errors=tuple(sorted(set(document.errors + validate_editor_document(document).errors))),
    )


def _record_change(
    document: EditorDocument,
    *,
    action: str,
    target_id: str,
    changed_fields: tuple[str, ...],
    chapters: tuple[EditorChapter, ...] | None = None,
    quests: tuple[EditorQuest, ...] | None = None,
    edges: tuple[EditorEdge, ...] | None = None,
) -> EditorDocument:
    revision = document.revision + 1
    dirty = tuple(sorted(set(document.dirty_entities + (target_id,))))
    change = EditorChange(revision, action, target_id, tuple(sorted(changed_fields)))
    return replace(
        document,
        revision=revision,
        chapters=chapters if chapters is not None else document.chapters,
        quests=quests if quests is not None else document.quests,
        edges=edges if edges is not None else document.edges,
        dirty_entities=dirty,
        change_log=document.change_log + (change,),
    )


def apply_editor_operation(
    document: EditorDocument,
    operation: EditorOperation,
) -> EditorTransaction:
    if operation.action not in EDITOR_OPERATION_TYPES:
        return EditorTransaction(
            document,
            document,
            operation,
            (f"unsupported editor operation: {operation.action}",),
        )
    values = operation.value_map()
    updated = document
    changed_fields: tuple[str, ...] = ()

    if operation.action == "update_chapter":
        allowed = {"title", "category", "order"}
        unknown = sorted(set(values) - allowed)
        if unknown:
            return EditorTransaction(
                document,
                document,
                operation,
                (f"unsupported chapter fields: {', '.join(unknown)}",),
            )
        found = False
        chapters: list[EditorChapter] = []
        for chapter in document.chapters:
            if chapter.chapter_id != operation.target_id:
                chapters.append(chapter)
                continue
            found = True
            changes = {
                key: (int(value) if key == "order" else str(value))
                for key, value in values.items()
            }
            chapters.append(replace(chapter, **changes))
        if not found:
            return EditorTransaction(
                document, document, operation, (f"unknown chapter: {operation.target_id}",)
            )
        changed_fields = tuple(values)
        updated = _record_change(
            document,
            action=operation.action,
            target_id=operation.target_id,
            changed_fields=changed_fields,
            chapters=tuple(sorted(chapters, key=lambda item: (item.order, item.chapter_id))),
        )

    elif operation.action in {"update_quest", "move_quest"}:
        allowed = (
            {"title", "description", "review_required", "reward_decision", "rewards"}
            if operation.action == "update_quest"
            else {"chapter_id", "order", "x", "y"}
        )
        unknown = sorted(set(values) - allowed)
        if unknown:
            return EditorTransaction(
                document,
                document,
                operation,
                (f"unsupported quest fields: {', '.join(unknown)}",),
            )
        found = False
        quests: list[EditorQuest] = []
        for quest in document.quests:
            if quest.quest_id != operation.target_id:
                quests.append(quest)
                continue
            found = True
            changes: dict[str, object] = {}
            for key, value in values.items():
                if key in {"order", "x", "y"}:
                    changes[key] = int(value)
                elif key == "review_required":
                    changes[key] = bool(value)
                elif key == "rewards":
                    if not isinstance(value, (list, tuple)):
                        return EditorTransaction(
                            document,
                            document,
                            operation,
                            ("quest rewards must be a list",),
                        )
                    parsed_rewards: list[EditorReward] = []
                    for index, item in enumerate(value):
                        if not isinstance(item, Mapping):
                            return EditorTransaction(
                                document,
                                document,
                                operation,
                                (f"quest reward {index + 1} must be an object",),
                            )
                        try:
                            reward = EditorReward.from_dict(item)
                        except (TypeError, ValueError) as exc:
                            return EditorTransaction(
                                document,
                                document,
                                operation,
                                (f"invalid quest reward {index + 1}: {exc}",),
                            )
                        if not reward.reward_type.strip() or not reward.identifier.strip():
                            return EditorTransaction(
                                document,
                                document,
                                operation,
                                (f"quest reward {index + 1} requires a type and id",),
                            )
                        if reward.count < 1:
                            return EditorTransaction(
                                document,
                                document,
                                operation,
                                (f"quest reward {index + 1} count must be at least 1",),
                            )
                        parsed_rewards.append(reward)
                    changes[key] = tuple(parsed_rewards)
                else:
                    changes[key] = str(value)
            resulting_decision = str(changes.get("reward_decision", quest.reward_decision))
            resulting_rewards = changes.get("rewards", quest.rewards)
            if resulting_decision == "rewarded" and not resulting_rewards:
                return EditorTransaction(
                    document,
                    document,
                    operation,
                    ("rewarded quests require at least one reward",),
                )
            if resulting_decision != "rewarded" and resulting_rewards:
                return EditorTransaction(
                    document,
                    document,
                    operation,
                    ("set reward decision to rewarded before adding rewards",),
                )
            quests.append(replace(quest, **changes))
        if not found:
            return EditorTransaction(
                document, document, operation, (f"unknown quest: {operation.target_id}",)
            )
        changed_fields = tuple(values)
        updated = _record_change(
            document,
            action=operation.action,
            target_id=operation.target_id,
            changed_fields=changed_fields,
            quests=tuple(quests),
        )

    else:
        prerequisite = str(values.get("prerequisite_id", ""))
        enabled = bool(values.get("enabled", True))
        if not prerequisite:
            return EditorTransaction(
                document, document, operation, ("prerequisite_id is required",)
            )
        if set(values) - {"prerequisite_id", "enabled"}:
            return EditorTransaction(
                document, document, operation, ("unsupported dependency fields",)
            )
        relation = (prerequisite, operation.target_id)
        existing = {
            (edge.prerequisite_quest, edge.dependent_quest): edge for edge in document.edges
        }
        if enabled:
            existing[relation] = EditorEdge.create(*relation)
        else:
            existing.pop(relation, None)
        edges = tuple(
            sorted(
                existing.values(),
                key=lambda item: (item.prerequisite_quest, item.dependent_quest),
            )
        )
        updated = _record_change(
            document,
            action=operation.action,
            target_id=operation.target_id,
            changed_fields=("dependency",),
            edges=edges,
        )

    if not changed_fields and operation.action != "set_dependency":
        return EditorTransaction(document, document, operation, ("operation contains no changes",))
    validation = validate_editor_document(updated)
    if validation.errors:
        return EditorTransaction(document, document, operation, validation.errors)
    return EditorTransaction(document, updated, operation)


def generate_editor_model(
    source: Path,
    *,
    target_quests: int | None = None,
    chapter_size: int = 40,
    description_style: str = "guided",
    reward_policy: str = "unassigned",
) -> EditorDocument:
    if reward_policy != "unassigned" and reward_policy not in REWARD_POLICIES:
        return EditorDocument(
            schema_version=EDITOR_SCHEMA_VERSION,
            revision=0,
            source_path=str(source),
            source_format="unknown",
            pack_name="",
            minecraft_version="",
            loader="",
            requested_quests=target_quests or 0,
            available_candidates=0,
            chapters=(),
            quests=(),
            edges=(),
            errors=(
                "reward policy must be unassigned or one of: " + ", ".join(REWARD_POLICIES),
            ),
        )
    if reward_policy == "unassigned":
        plan = generate_quest_description_plan(
            source,
            target_quests=target_quests,
            chapter_size=chapter_size,
            style=description_style,
        )
        return build_editor_document(plan.blueprint)
    plan = generate_quest_reward_plan(
        source,
        target_quests=target_quests,
        chapter_size=chapter_size,
        policy=reward_policy,
        description_style=description_style,
    )
    return build_editor_document(plan.blueprint)
