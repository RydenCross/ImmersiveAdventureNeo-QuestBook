import json

import pytest

from content import create_project
from generator.cli import main
from generator.progression_metrics import _longest_depths, analyze_progression


def test_authored_progression_metrics_are_stable() -> None:
    report = analyze_progression(create_project())
    assert report.chapters == 13
    assert report.quests == 656
    assert report.dependencies == 867
    assert report.maximum_depth > 20
    assert report.deepest_quests


def test_metrics_identify_bottlenecks_and_transitions() -> None:
    report = analyze_progression(create_project())
    assert report.bottlenecks
    assert all(int(item["dependants"]) >= 4 for item in report.bottlenecks)
    assert report.chapter_transitions
    assert all(item["from_chapter"] != item["to_chapter"] for item in report.chapter_transitions)


def test_cli_writes_machine_readable_metrics(tmp_path) -> None:
    output = tmp_path / "progression-metrics.json"
    assert main(["progression-metrics", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["quests"] == 656
    assert payload["maximum_depth"] > 20


def test_metrics_reject_cycles() -> None:
    incoming = {"a": {"b"}, "b": {"a"}}
    outgoing = {"a": {"b"}, "b": {"a"}}
    with pytest.raises(ValueError, match="acyclic"):
        _longest_depths(incoming, outgoing)
