from model import Project

from content.create.foundations import build_create_foundations
from content.create.processing import build_create_processing


def build_create(project: Project, mining_complete: str) -> str:
    create, foundations_complete = build_create_foundations(project, mining_complete)
    return build_create_processing(create, foundations_complete)


__all__ = ["build_create"]
