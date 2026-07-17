from model import Project

from content.create.automation import build_create_automation
from content.create.foundations import build_create_foundations
from content.create.logistics_trains import build_create_logistics_and_trains
from content.create.processing import build_create_processing


def build_create(project: Project, mining_complete: str) -> str:
    create, foundations_complete = build_create_foundations(project, mining_complete)
    processing_complete = build_create_processing(create, foundations_complete)
    automation_complete = build_create_automation(create, processing_complete)
    return build_create_logistics_and_trains(create, automation_complete)


__all__ = ["build_create"]
