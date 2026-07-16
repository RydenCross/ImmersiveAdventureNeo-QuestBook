from dataclasses import dataclass, field
from model.chapter import Chapter
from model.quest import Quest

@dataclass(slots=True)
class Project:
    name: str
    version: str
    chapters: list[Chapter] = field(default_factory=list)
    language: dict[str, str] = field(default_factory=dict)

    def add_chapter(self, chapter: Chapter) -> None:
        if self.get_chapter(chapter.id) is not None:
            raise ValueError(f"Duplicate chapter id: {chapter.id}")
        self.chapters.append(chapter)

    def get_chapter(self, chapter_id: str) -> Chapter | None:
        return next((c for c in self.chapters if c.id == chapter_id), None)

    def get_quest(self, quest_id: str) -> Quest | None:
        for chapter in self.chapters:
            quest = chapter.get_quest(quest_id)
            if quest is not None:
                return quest
        return None

    @property
    def quests(self) -> list[Quest]:
        return [q for chapter in self.chapters for q in chapter.quests]
