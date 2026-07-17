from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from content import create_project
from model.project import Project

DEFAULT_IDENTITY_BASELINE_PATH = Path("reports/quest-identity-baseline.json")


@dataclass(frozen=True, slots=True)
class IdentityManifest:
    chapters: tuple[dict[str, object], ...]
    quests: tuple[dict[str, object], ...]

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def quest_count(self) -> int:
        return len(self.quests)

    def to_dict(self) -> dict[str, object]:
        return {
            "chapter_count": self.chapter_count,
            "quest_count": self.quest_count,
            "chapters": list(self.chapters),
            "quests": list(self.quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class IdentityGuardResult:
    baseline: IdentityManifest
    current: IdentityManifest
    missing_chapters: tuple[str, ...]
    changed_chapters: tuple[str, ...]
    missing_quests: tuple[str, ...]
    changed_quests: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_chapters,
                self.changed_chapters,
                self.missing_quests,
                self.changed_quests,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "baseline": {
                "chapters": self.baseline.chapter_count,
                "quests": self.baseline.quest_count,
            },
            "current": {
                "chapters": self.current.chapter_count,
                "quests": self.current.quest_count,
            },
            "missing_chapters": list(self.missing_chapters),
            "changed_chapters": list(self.changed_chapters),
            "missing_quests": list(self.missing_quests),
            "changed_quests": list(self.changed_quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest identity guard: {'PASS' if self.is_clean else 'FAIL'}",
            f"Chapters: {self.current.chapter_count} current / {self.baseline.chapter_count} protected.",
            f"Quests: {self.current.quest_count} current / {self.baseline.quest_count} protected.",
            f"Missing chapters: {len(self.missing_chapters)}.",
            f"Changed chapter identities: {len(self.changed_chapters)}.",
            f"Missing quests: {len(self.missing_quests)}.",
            f"Changed quest identities: {len(self.changed_quests)}.",
        ]
        lines.extend(f"Missing chapter: {value}" for value in self.missing_chapters)
        lines.extend(f"Changed chapter: {value}" for value in self.changed_chapters)
        lines.extend(f"Missing quest: {value}" for value in self.missing_quests)
        lines.extend(f"Changed quest: {value}" for value in self.changed_quests)
        return "\n".join(lines)


def build_identity_manifest(project: Project) -> IdentityManifest:
    chapters: list[dict[str, object]] = []
    quests: list[dict[str, object]] = []
    for chapter in project.chapters:
        chapters.append(
            {
                "id": chapter.id,
                "ftb_id": chapter.ftb_id,
                "title": chapter.title,
            }
        )
        for quest in chapter.quests:
            quests.append(
                {
                    "id": quest.id,
                    "ftb_id": quest.ftb_id,
                    "uuid": str(quest.uuid),
                    "chapter_id": chapter.id,
                    "title": quest.title,
                }
            )
    return IdentityManifest(
        chapters=tuple(sorted(chapters, key=lambda item: str(item["id"]))),
        quests=tuple(sorted(quests, key=lambda item: str(item["id"]))),
    )


def load_identity_manifest(path: Path = DEFAULT_IDENTITY_BASELINE_PATH) -> IdentityManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Quest identity baseline not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid quest identity baseline JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid quest identity baseline.")
    chapters = payload.get("chapters")
    quests = payload.get("quests")
    if not isinstance(chapters, list) or not isinstance(quests, list):
        raise ValueError("Invalid quest identity baseline.")
    if not all(isinstance(item, dict) for item in chapters + quests):
        raise ValueError("Invalid quest identity baseline entries.")
    return IdentityManifest(tuple(chapters), tuple(quests))


def compare_identity_manifests(
    baseline: IdentityManifest, current: IdentityManifest
) -> IdentityGuardResult:
    baseline_chapters = {str(item["id"]): item for item in baseline.chapters}
    current_chapters = {str(item["id"]): item for item in current.chapters}
    baseline_quests = {str(item["id"]): item for item in baseline.quests}
    current_quests = {str(item["id"]): item for item in current.quests}

    missing_chapters = tuple(sorted(set(baseline_chapters) - set(current_chapters)))
    missing_quests = tuple(sorted(set(baseline_quests) - set(current_quests)))
    changed_chapters = tuple(
        sorted(
            chapter_id
            for chapter_id in set(baseline_chapters) & set(current_chapters)
            if baseline_chapters[chapter_id] != current_chapters[chapter_id]
        )
    )
    changed_quests = tuple(
        sorted(
            quest_id
            for quest_id in set(baseline_quests) & set(current_quests)
            if baseline_quests[quest_id] != current_quests[quest_id]
        )
    )
    return IdentityGuardResult(
        baseline,
        current,
        missing_chapters,
        changed_chapters,
        missing_quests,
        changed_quests,
    )


def run_identity_guard(
    baseline_path: Path = DEFAULT_IDENTITY_BASELINE_PATH,
) -> IdentityGuardResult:
    return compare_identity_manifests(
        load_identity_manifest(baseline_path), build_identity_manifest(create_project())
    )


def refresh_identity_baseline(
    destination: Path = DEFAULT_IDENTITY_BASELINE_PATH,
) -> IdentityManifest:
    manifest = build_identity_manifest(create_project())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(manifest.format_json() + "\n", encoding="utf-8")
    return manifest
