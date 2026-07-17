from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import re

from content import create_project
from model import Project

_PLACEHOLDER = re.compile(r"\b(?:todo|tbd|fixme|lorem ipsum|placeholder|coming soon)\b", re.IGNORECASE)
_BAD_WHITESPACE = re.compile(r"[ \t]+\n|\n[ \t]+|[ \t]{2,}")


@dataclass(frozen=True, slots=True)
class TextAudit:
    quest_count: int
    chapter_count: int
    placeholder_text: tuple[str, ...]
    malformed_text: tuple[str, ...]
    duplicate_descriptions: tuple[str, ...]
    suspiciously_short_descriptions: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.placeholder_text, self.malformed_text, self.duplicate_descriptions))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "chapter_count": self.chapter_count,
            "quest_count": self.quest_count,
            "placeholder_text": list(self.placeholder_text),
            "malformed_text": list(self.malformed_text),
            "duplicate_descriptions": list(self.duplicate_descriptions),
            "suspiciously_short_descriptions": list(self.suspiciously_short_descriptions),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest text quality audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checked {self.quest_count} quests across {self.chapter_count} chapters.",
            f"Placeholder text: {len(self.placeholder_text)}.",
            f"Malformed text: {len(self.malformed_text)}.",
            f"Duplicate descriptions: {len(self.duplicate_descriptions)}.",
            f"Short descriptions for review: {len(self.suspiciously_short_descriptions)}.",
        ]
        lines.extend(f"Placeholder: {value}" for value in self.placeholder_text)
        lines.extend(f"Malformed: {value}" for value in self.malformed_text)
        lines.extend(f"Duplicate: {value}" for value in self.duplicate_descriptions)
        lines.extend(f"Review: {value}" for value in self.suspiciously_short_descriptions)
        return "\n".join(lines)


def _malformed_reason(text: str) -> str | None:
    if text != text.strip():
        return "leading or trailing whitespace"
    if _BAD_WHITESPACE.search(text):
        return "irregular whitespace"
    if text.count("`") % 2:
        return "unbalanced backticks"
    if text.count("[") != text.count("]"):
        return "unbalanced square brackets"
    if "\x00" in text:
        return "contains a NUL character"
    return None


def audit_text(project: Project) -> TextAudit:
    placeholders: list[str] = []
    malformed: list[str] = []
    short: list[str] = []
    descriptions: defaultdict[str, list[str]] = defaultdict(list)

    for chapter in project.chapters:
        fields = ((f"chapter {chapter.id} title", chapter.title), (f"chapter {chapter.id} description", chapter.description))
        for label, text in fields:
            if _PLACEHOLDER.search(text):
                placeholders.append(label)
            reason = _malformed_reason(text)
            if reason:
                malformed.append(f"{label}: {reason}")

        for quest in chapter.quests:
            label = f"{chapter.id}/{quest.id}"
            for field_name, text in (("title", quest.title), ("description", quest.description)):
                if _PLACEHOLDER.search(text):
                    placeholders.append(f"{label} {field_name}")
                reason = _malformed_reason(text)
                if reason:
                    malformed.append(f"{label} {field_name}: {reason}")
            normalized = " ".join(quest.description.casefold().split())
            if len(normalized) >= 40:
                descriptions[normalized].append(label)
            if 0 < len(normalized) < 20:
                short.append(f"{label}: {len(normalized)} characters")

    duplicates = tuple(
        sorted(
            f"{', '.join(sorted(ids))} share the same description"
            for ids in descriptions.values()
            if len(ids) > 1
        )
    )
    return TextAudit(
        quest_count=len(project.quests),
        chapter_count=len(project.chapters),
        placeholder_text=tuple(sorted(placeholders)),
        malformed_text=tuple(sorted(malformed)),
        duplicate_descriptions=duplicates,
        suspiciously_short_descriptions=tuple(sorted(short)),
    )


def run_text_audit() -> TextAudit:
    return audit_text(create_project())
