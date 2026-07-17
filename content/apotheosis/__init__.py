from model import Project

from content.apotheosis.foundations import build_apotheosis_foundations


def build_apotheosis(project: Project, ars_complete: str) -> str:
    return build_apotheosis_foundations(project, ars_complete)


__all__ = ["build_apotheosis"]
