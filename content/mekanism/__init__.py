from model import Project

from content.mekanism.foundations import build_mekanism_foundations


def build_mekanism(project: Project, ae2_complete: str) -> str:
    return build_mekanism_foundations(project, ae2_complete)


__all__ = ["build_mekanism"]
