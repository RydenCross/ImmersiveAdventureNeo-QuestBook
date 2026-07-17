from model import Project

from content.ae2.foundations import build_ae2_foundations


def build_ae2(project: Project, apotheosis_complete: str) -> str:
    return build_ae2_foundations(project, apotheosis_complete)


__all__ = ["build_ae2"]
