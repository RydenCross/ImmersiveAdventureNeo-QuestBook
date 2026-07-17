from model import Project

from content.ae2.advanced_storage_networking import (
    build_ae2_advanced_storage_networking,
)
from content.ae2.channels_autocrafting import build_ae2_channels_autocrafting
from content.ae2.foundations import build_ae2_foundations
from content.ae2.quantum_engineering import build_ae2_quantum_engineering


def build_ae2(project: Project, apotheosis_complete: str) -> str:
    chapter, foundations_complete = build_ae2_foundations(project, apotheosis_complete)
    autocrafting_complete = build_ae2_channels_autocrafting(
        chapter, foundations_complete
    )
    mastery = build_ae2_advanced_storage_networking(chapter, autocrafting_complete)
    build_ae2_quantum_engineering(chapter, mastery)
    return mastery


__all__ = ["build_ae2"]
