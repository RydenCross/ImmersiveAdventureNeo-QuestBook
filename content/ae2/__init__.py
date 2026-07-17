from model import Project

from content.ae2.channels_autocrafting import build_ae2_channels_autocrafting
from content.ae2.foundations import build_ae2_foundations


def build_ae2(project: Project, apotheosis_complete: str) -> str:
    chapter, foundations_complete = build_ae2_foundations(project, apotheosis_complete)
    return build_ae2_channels_autocrafting(chapter, foundations_complete)


__all__ = ["build_ae2"]
