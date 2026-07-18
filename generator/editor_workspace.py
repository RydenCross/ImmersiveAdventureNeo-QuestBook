from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Iterable

from generator.editor_model import (
    EditorChange,
    EditorDocument,
    EditorOperation,
    EditorQuest,
    apply_editor_operation,
    validate_editor_document,
)

MAX_BATCH_OPERATIONS = 1000
MAX_LAYOUT_SPACING = 20


@dataclass(frozen=True, slots=True)
class EditorBatchTransaction:
    before: EditorDocument
    after: EditorDocument
    operations: tuple[EditorOperation, ...]
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return bool(self.operations) and not self.errors and self.after.revision > self.before.revision

    def undo(self) -> EditorDocument:
        return self.before

    def redo(self) -> EditorDocument:
        return self.after


@dataclass(frozen=True, slots=True)
class EditorAutoLayout:
    document: EditorDocument
    changed_quests: tuple[str, ...]
    laid_out_chapters: tuple[str, ...]
    depth_levels: int
    collisions: tuple[str, ...]
    errors: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.errors and not self.collisions

    @property
    def changed(self) -> bool:
        return bool(self.changed_quests)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "changed": self.changed,
            "changed_quests": list(self.changed_quests),
            "laid_out_chapters": list(self.laid_out_chapters),
            "depth_levels": self.depth_levels,
            "collisions": list(self.collisions),
            "errors": list(self.errors),
            "document": self.document.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def apply_editor_batch(
    document: EditorDocument,
    operations: Iterable[EditorOperation],
) -> EditorBatchTransaction:
    operation_list = tuple(operations)
    if not operation_list:
        return EditorBatchTransaction(document, document, (), ("batch must contain operations",))
    if len(operation_list) > MAX_BATCH_OPERATIONS:
        return EditorBatchTransaction(
            document,
            document,
            operation_list,
            (f"batch exceeds {MAX_BATCH_OPERATIONS} operations",),
        )

    current = document
    for index, operation in enumerate(operation_list):
        transaction = apply_editor_operation(current, operation)
        if not transaction.is_clean:
            detail = "; ".join(transaction.errors) or "operation did not change the document"
            return EditorBatchTransaction(
                document,
                document,
                operation_list,
                (f"operation {index + 1} rejected: {detail}",),
            )
        current = transaction.after
    return EditorBatchTransaction(document, current, operation_list)


def _quest_depths(document: EditorDocument) -> dict[str, int]:
    quest_ids = {quest.quest_id for quest in document.quests}
    incoming: dict[str, set[str]] = {identifier: set() for identifier in quest_ids}
    outgoing: dict[str, set[str]] = {identifier: set() for identifier in quest_ids}
    for edge in document.edges:
        if edge.prerequisite_quest in quest_ids and edge.dependent_quest in quest_ids:
            incoming[edge.dependent_quest].add(edge.prerequisite_quest)
            outgoing[edge.prerequisite_quest].add(edge.dependent_quest)

    ready = sorted(identifier for identifier, prerequisites in incoming.items() if not prerequisites)
    depths = {identifier: 0 for identifier in ready}
    visited: set[str] = set()
    while ready:
        identifier = ready.pop(0)
        visited.add(identifier)
        for dependent in sorted(outgoing[identifier]):
            depths[dependent] = max(depths.get(dependent, 0), depths[identifier] + 1)
            incoming[dependent].discard(identifier)
            if not incoming[dependent]:
                ready.append(dependent)
                ready.sort()
    for identifier in sorted(quest_ids - visited):
        depths.setdefault(identifier, 0)
    return depths


def _layout_collisions(quests: tuple[EditorQuest, ...]) -> tuple[str, ...]:
    positions: dict[tuple[str, int, int], list[str]] = {}
    for quest in quests:
        positions.setdefault((quest.chapter_id, quest.x, quest.y), []).append(quest.quest_id)
    return tuple(
        f"{chapter_id}:{x},{y}:{','.join(sorted(identifiers))}"
        for (chapter_id, x, y), identifiers in sorted(positions.items())
        if len(identifiers) > 1
    )


def auto_layout_editor_document(
    document: EditorDocument,
    *,
    chapter_id: str | None = None,
    horizontal_spacing: int = 1,
    vertical_spacing: int = 1,
) -> EditorAutoLayout:
    validation = validate_editor_document(document)
    if validation.errors:
        return EditorAutoLayout(
            document,
            (),
            (),
            0,
            (),
            ("cannot lay out an invalid editor document", *validation.errors),
        )
    if not 1 <= horizontal_spacing <= MAX_LAYOUT_SPACING:
        return EditorAutoLayout(
            document,
            (),
            (),
            0,
            (),
            (f"horizontal_spacing must be between 1 and {MAX_LAYOUT_SPACING}",),
        )
    if not 1 <= vertical_spacing <= MAX_LAYOUT_SPACING:
        return EditorAutoLayout(
            document,
            (),
            (),
            0,
            (),
            (f"vertical_spacing must be between 1 and {MAX_LAYOUT_SPACING}",),
        )

    chapter_ids = {chapter.chapter_id for chapter in document.chapters}
    if chapter_id is not None and chapter_id not in chapter_ids:
        return EditorAutoLayout(
            document,
            (),
            (),
            0,
            (),
            (f"unknown chapter: {chapter_id}",),
        )
    selected_chapters = tuple(
        chapter.chapter_id
        for chapter in sorted(document.chapters, key=lambda item: (item.order, item.chapter_id))
        if chapter_id is None or chapter.chapter_id == chapter_id
    )
    selected_set = set(selected_chapters)
    depths = _quest_depths(document)

    coordinates: dict[str, tuple[int, int]] = {}
    for selected in selected_chapters:
        chapter_quests = [quest for quest in document.quests if quest.chapter_id == selected]
        by_depth: dict[int, list[EditorQuest]] = {}
        for quest in chapter_quests:
            by_depth.setdefault(depths.get(quest.quest_id, 0), []).append(quest)
        for depth, quests in sorted(by_depth.items()):
            for row, quest in enumerate(sorted(quests, key=lambda item: (item.order, item.quest_id))):
                coordinates[quest.quest_id] = (
                    depth * horizontal_spacing,
                    row * vertical_spacing,
                )

    changed: list[str] = []
    updated_quests: list[EditorQuest] = []
    for quest in document.quests:
        coordinate = coordinates.get(quest.quest_id)
        if quest.chapter_id not in selected_set or coordinate is None:
            updated_quests.append(quest)
            continue
        x, y = coordinate
        if (quest.x, quest.y) != (x, y):
            changed.append(quest.quest_id)
            updated_quests.append(replace(quest, x=x, y=y))
        else:
            updated_quests.append(quest)

    quest_tuple = tuple(updated_quests)
    collisions = _layout_collisions(quest_tuple)
    if collisions:
        return EditorAutoLayout(
            document,
            tuple(sorted(changed)),
            selected_chapters,
            max(depths.values(), default=-1) + 1,
            collisions,
            ("automatic layout produced coordinate collisions",),
        )

    updated = document
    if changed:
        revision = document.revision + 1
        target = chapter_id or "all-chapters"
        updated = replace(
            document,
            revision=revision,
            quests=quest_tuple,
            dirty_entities=tuple(sorted(set(document.dirty_entities).union(changed))),
            change_log=document.change_log
            + (
                EditorChange(
                    revision=revision,
                    action="auto_layout",
                    target_id=target,
                    changed_fields=("position",),
                ),
            ),
        )
        updated_validation = validate_editor_document(updated)
        if updated_validation.errors:
            return EditorAutoLayout(
                document,
                tuple(sorted(changed)),
                selected_chapters,
                max(depths.values(), default=-1) + 1,
                (),
                updated_validation.errors,
            )

    return EditorAutoLayout(
        updated,
        tuple(sorted(changed)),
        selected_chapters,
        max(depths.values(), default=-1) + 1,
        (),
    )
