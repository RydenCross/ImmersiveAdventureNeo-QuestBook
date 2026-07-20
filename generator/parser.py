from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from generator.snbt import loads
from model import (
    Chapter,
    Dependency,
    Difficulty,
    Position,
    Project,
    Quest,
    Reward,
    RewardType,
    Task,
    TaskType,
)


def ftb_id_to_uuid(ftb_id: str) -> UUID:
    return UUID(int=int(ftb_id, 16))


class FTBQuestParser:
    def load(self, root: str | Path) -> Project:
        root_path = Path(root)
        quests_root = root_path / "quests" if (root_path / "quests").is_dir() else root_path
        data = self._read(quests_root / "data.snbt")
        language = self._read(quests_root / "lang" / f"{data.get('fallback_locale', 'en_us')}.snbt")
        project = Project(
            name="Immersive Adventure Neo",
            version=str(data.get("version", "unknown")),
            language={str(k): str(v) for k, v in language.items()},
        )
        for chapter_file in sorted((quests_root / "chapters").glob("*.snbt")):
            project.add_chapter(self._chapter(self._read(chapter_file), project.language))
        return project

    @staticmethod
    def _read(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        parsed = loads(path.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected compound root in {path}")
        return parsed

    def _chapter(self, raw: dict[str, Any], lang: dict[str, str]) -> Chapter:
        ftb_id = str(raw["id"])
        chapter = Chapter(
            id=str(raw.get("filename", ftb_id.lower())),
            uuid=ftb_id_to_uuid(ftb_id),
            title=lang.get(f"chapter.{ftb_id}.title", str(raw.get("filename", ftb_id))),
            icon=str(raw.get("icon", "minecraft:book")),
            group=str(raw.get("group", "")) or None,
            description=lang.get(f"chapter.{ftb_id}.subtitle", ""),
            ftb_id=ftb_id,
            raw_data=raw,
        )
        for quest_raw in raw.get("quests", []):
            chapter.add_quest(self._quest(quest_raw, lang))
        return chapter

    def _quest(self, raw: dict[str, Any], lang: dict[str, str]) -> Quest:
        ftb_id = str(raw["id"])
        dependencies = [Dependency(str(parent)) for parent in raw.get("dependencies", [])]
        tasks = [self._task(task) for task in raw.get("tasks", [])]
        rewards = [self._reward(reward) for reward in raw.get("rewards", [])]
        return Quest(
            id=ftb_id,
            uuid=ftb_id_to_uuid(ftb_id),
            title=lang.get(f"quest.{ftb_id}.title", ftb_id),
            description=lang.get(f"quest.{ftb_id}.subtitle", ""),
            icon=str(raw.get("icon", "minecraft:paper")),
            tasks=tasks,
            rewards=rewards,
            dependencies=dependencies,
            position=Position(float(raw.get("x", 0.0)), float(raw.get("y", 0.0))),
            difficulty=Difficulty.NORMAL,
            hidden=bool(raw.get("hide", False)),
            repeatable=bool(raw.get("repeatable", False)),
            optional=bool(raw.get("optional", False)),
            ftb_id=ftb_id,
            raw_data=raw,
        )

    @staticmethod
    def _task(raw: dict[str, Any]) -> Task:
        task_type_raw = str(raw.get("type", "custom"))
        task_type = (
            TaskType(task_type_raw)
            if task_type_raw in TaskType._value2member_map_
            else TaskType.CUSTOM
        )
        ftb_id = str(raw.get("id", ""))
        return Task(
            id=ftb_id,
            type=task_type,
            data={k: v for k, v in raw.items() if k not in {"id", "type"}},
            raw_data=raw,
        )

    @staticmethod
    def _reward(raw: dict[str, Any]) -> Reward:
        reward_type_raw = str(raw.get("type", "custom"))
        reward_type = (
            RewardType(reward_type_raw)
            if reward_type_raw in RewardType._value2member_map_
            else RewardType.CUSTOM
        )
        ftb_id = str(raw.get("id", ""))
        return Reward(
            id=ftb_id,
            type=reward_type,
            data={k: v for k, v in raw.items() if k not in {"id", "type"}},
            raw_data=raw,
        )
