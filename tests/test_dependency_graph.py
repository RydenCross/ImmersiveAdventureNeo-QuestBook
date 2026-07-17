import json

from content import create_project
from generator.cli import main
from generator.dependency_graph import build_dependency_graph


def test_authored_graph_totals() -> None:
    graph = build_dependency_graph(create_project())
    assert len(graph.nodes) == 656
    assert len(graph.edges) == 867
    assert len(graph.chapters) == 13


def test_graph_json_contains_chapter_and_optional_metadata() -> None:
    payload = json.loads(build_dependency_graph(create_project()).format_json())
    assert payload["chapters"][0]["id"] == "00_welcome"
    assert any(node["optional"] for node in payload["nodes"])


def test_graph_dot_contains_clusters_and_edges() -> None:
    dot = build_dependency_graph(create_project()).format_dot()
    assert 'digraph quest_progression' in dot
    assert 'subgraph "cluster_00_welcome"' in dot
    assert '->' in dot


def test_cli_writes_dot_and_json(tmp_path) -> None:
    dot = tmp_path / "dependency-graph.dot"
    js = tmp_path / "dependency-graph.json"
    assert main(["dependency-graph", "--output", str(dot)]) == 0
    assert main(["dependency-graph", "--format", "json", "--output", str(js)]) == 0
    assert dot.read_text().startswith("digraph quest_progression")
    assert len(json.loads(js.read_text())["nodes"]) == 656
