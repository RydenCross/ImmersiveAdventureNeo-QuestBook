from model import Project

from content.actually_additions.foundations import build_actually_additions_foundations


def build_actually_additions(project: Project, create_complete: str) -> str:
    return build_actually_additions_foundations(project, create_complete)


__all__ = ["build_actually_additions"]
