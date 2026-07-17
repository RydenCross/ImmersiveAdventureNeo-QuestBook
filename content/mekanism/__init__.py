from model import Project

from content.mekanism.factories_advanced_processing import (
    build_mekanism_factories_advanced_processing,
)
from content.mekanism.endgame_mastery import build_mekanism_endgame_mastery
from content.mekanism.foundations import build_mekanism_foundations
from content.mekanism.power_reactors import build_mekanism_power_reactors


def build_mekanism(project: Project, ae2_complete: str) -> str:
    chapter, foundations_complete = build_mekanism_foundations(project, ae2_complete)
    processing_complete = build_mekanism_factories_advanced_processing(
        chapter, foundations_complete
    )
    stable_reactor = build_mekanism_power_reactors(chapter, processing_complete)
    build_mekanism_endgame_mastery(chapter, stable_reactor)
    return stable_reactor


__all__ = ["build_mekanism"]
