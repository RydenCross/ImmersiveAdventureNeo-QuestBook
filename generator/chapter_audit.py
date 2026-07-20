from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import re

from content import create_project
from model import Project

_RESOURCE_LOCATION = re.compile(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$")
_CHAPTER_ID = re.compile(r"^\d{2}_[a-z0-9_]+$")
_FTB_ID = re.compile(r"^[0-9A-F]{16}$")


@dataclass(frozen=True, slots=True)
class ChapterAudit:
    chapter_count: int
    quest_count: int
    chapter_sizes: dict[str, int]
    duplicate_uuids: tuple[str, ...]
    duplicate_ftb_ids: tuple[str, ...]
    duplicate_titles: tuple[str, ...]
    invalid_chapters: tuple[str, ...]
    empty_chapters: tuple[str, ...]
    order_issues: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.duplicate_uuids,
                self.duplicate_ftb_ids,
                self.duplicate_titles,
                self.invalid_chapters,
                self.empty_chapters,
                self.order_issues,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "chapter_count": self.chapter_count,
            "quest_count": self.quest_count,
            "chapter_sizes": dict(sorted(self.chapter_sizes.items())),
            "duplicate_uuids": list(self.duplicate_uuids),
            "duplicate_ftb_ids": list(self.duplicate_ftb_ids),
            "duplicate_titles": list(self.duplicate_titles),
            "invalid_chapters": list(self.invalid_chapters),
            "empty_chapters": list(self.empty_chapters),
            "order_issues": list(self.order_issues),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Chapter integrity audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Chapters: {self.chapter_count} containing {self.quest_count} quest(s).",
            f"Duplicate UUIDs: {len(self.duplicate_uuids)}.",
            f"Duplicate FTB IDs: {len(self.duplicate_ftb_ids)}.",
            f"Duplicate titles: {len(self.duplicate_titles)}.",
            f"Invalid chapter definitions: {len(self.invalid_chapters)}.",
            f"Empty chapters: {len(self.empty_chapters)}.",
            f"Order issues: {len(self.order_issues)}.",
        ]
        lines.extend(f"Duplicate UUID: {value}" for value in self.duplicate_uuids)
        lines.extend(f"Duplicate FTB ID: {value}" for value in self.duplicate_ftb_ids)
        lines.extend(f"Duplicate title: {value}" for value in self.duplicate_titles)
        lines.extend(f"Invalid chapter: {value}" for value in self.invalid_chapters)
        lines.extend(f"Empty chapter: {value}" for value in self.empty_chapters)
        lines.extend(f"Order issue: {value}" for value in self.order_issues)
        return "\n".join(lines)


def _duplicates(values: defaultdict[str, list[str]]) -> tuple[str, ...]:
    return tuple(
        sorted(
            f"{value} ({', '.join(sorted(chapter_ids))})"
            for value, chapter_ids in values.items()
            if value and len(chapter_ids) > 1
        )
    )


def audit_chapters(project: Project) -> ChapterAudit:
    uuids: defaultdict[str, list[str]] = defaultdict(list)
    ftb_ids: defaultdict[str, list[str]] = defaultdict(list)
    titles: defaultdict[str, list[str]] = defaultdict(list)
    invalid: list[str] = []
    empty: list[str] = []
    order_issues: list[str] = []
    sizes: dict[str, int] = {}
    order_values: list[int] = []

    for expected_order, chapter in enumerate(project.chapters):
        chapter_id = chapter.id
        sizes[chapter_id] = len(chapter.quests)
        uuids[str(chapter.uuid)].append(chapter_id)
        ftb_ids[str(chapter.ftb_id or "")].append(chapter_id)
        titles[chapter.title.casefold()].append(chapter_id)

        if not _CHAPTER_ID.fullmatch(chapter_id):
            invalid.append(f"{chapter_id}: ID must match NN_slug")
        if not chapter.ftb_id or not _FTB_ID.fullmatch(chapter.ftb_id):
            invalid.append(f"{chapter_id}: invalid FTB ID {chapter.ftb_id!r}")
        if chapter.ftb_id and chapter.ftb_id != f"{chapter.uuid.int & ((1 << 64) - 1):016X}":
            invalid.append(f"{chapter_id}: FTB ID does not match UUID")
        if not _RESOURCE_LOCATION.fullmatch(chapter.icon):
            invalid.append(f"{chapter_id}: invalid icon {chapter.icon!r}")
        if not chapter.description.strip():
            invalid.append(f"{chapter_id}: description is empty")
        if not chapter.quests:
            empty.append(chapter_id)

        order = chapter.raw_data.get("order_index")
        if isinstance(order, bool) or not isinstance(order, int):
            order_issues.append(f"{chapter_id}: order_index must be an integer")
        else:
            order_values.append(order)
            if order != expected_order:
                order_issues.append(
                    f"{chapter_id}: order_index is {order}, expected {expected_order}"
                )

    order_counts = Counter(order_values)
    for order, count in sorted(order_counts.items()):
        if count > 1:
            order_issues.append(f"order_index {order} is used by {count} chapters")

    return ChapterAudit(
        chapter_count=len(project.chapters),
        quest_count=len(project.quests),
        chapter_sizes=sizes,
        duplicate_uuids=_duplicates(uuids),
        duplicate_ftb_ids=_duplicates(ftb_ids),
        duplicate_titles=_duplicates(titles),
        invalid_chapters=tuple(sorted(invalid)),
        empty_chapters=tuple(sorted(empty)),
        order_issues=tuple(sorted(order_issues)),
    )


def run_chapter_audit() -> ChapterAudit:
    return audit_chapters(create_project())
