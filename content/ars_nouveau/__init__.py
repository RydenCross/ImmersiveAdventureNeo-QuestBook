from model import Project

from content.ars_nouveau.foundations import build_ars_nouveau_foundations


def build_ars_nouveau(project: Project, actually_additions_complete: str) -> str:
    return build_ars_nouveau_foundations(project, actually_additions_complete)


__all__ = ["build_ars_nouveau"]
