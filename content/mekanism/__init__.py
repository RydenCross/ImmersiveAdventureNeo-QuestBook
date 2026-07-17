from model import Project

from content.mekanism.factories_advanced_processing import (
    build_mekanism_factories_advanced_processing,
)
from content.mekanism.foundations import build_mekanism_foundations


def build_mekanism(project: Project, ae2_complete: str) -> str:
    chapter, foundations_complete = build_mekanism_foundations(project, ae2_complete)
    return build_mekanism_factories_advanced_processing(chapter, foundations_complete)


__all__ = ["build_mekanism"]
