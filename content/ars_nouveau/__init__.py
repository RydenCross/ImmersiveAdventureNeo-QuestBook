from model import Project

from content.ars_nouveau.archmage_workshop import build_ars_nouveau_archmage_workshop
from content.ars_nouveau.foundations import build_ars_nouveau_foundations
from content.ars_nouveau.spellcraft_equipment import build_ars_nouveau_spellcraft_equipment


def build_ars_nouveau(project: Project, actually_additions_complete: str) -> str:
    ars, foundations_complete = build_ars_nouveau_foundations(
        project, actually_additions_complete
    )
    spellcraft_complete = build_ars_nouveau_spellcraft_equipment(
        ars, foundations_complete
    )
    build_ars_nouveau_archmage_workshop(ars, spellcraft_complete)
    return spellcraft_complete


__all__ = ["build_ars_nouveau"]
