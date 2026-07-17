from model import Project

from content.actually_additions.foundations import build_actually_additions_foundations
from content.actually_additions.machines_resources import (
    build_actually_additions_machines_resources,
)


def build_actually_additions(project: Project, create_complete: str) -> str:
    foundations_complete = build_actually_additions_foundations(project, create_complete)
    chapter = project.get_chapter("05_actually_additions")
    if chapter is None:
        raise RuntimeError("Actually Additions chapter was not created")

    # Reuse the existing chapter through a lightweight builder wrapper.
    from generator.builder import ChapterBuilder

    builder = object.__new__(ChapterBuilder)
    builder.project = project
    builder.slug = "05_actually_additions"
    builder.title = chapter.title
    builder.icon = chapter.icon
    builder.description = chapter.description
    from generator.ids import UUIDService
    builder.ids = UUIDService()
    builder.chapter = chapter

    return build_actually_additions_machines_resources(builder, foundations_complete)


__all__ = ["build_actually_additions"]
