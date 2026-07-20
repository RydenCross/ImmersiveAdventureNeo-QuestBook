from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from model.project import Project


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    nodes: tuple[dict[str, object], ...]
    edges: tuple[dict[str, str], ...]
    chapters: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format_dot(self) -> str:
        lines = [
            "digraph quest_progression {",
            "  rankdir=LR;",
            '  graph [compound=true, fontname="Helvetica"];',
            '  node [shape=box, fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
        ]
        nodes_by_chapter: dict[str, list[dict[str, object]]] = {}
        for node in self.nodes:
            nodes_by_chapter.setdefault(str(node["chapter_id"]), []).append(node)
        for chapter in self.chapters:
            chapter_id = str(chapter["id"])
            lines.append(f'  subgraph "cluster_{_escape(chapter_id)}" {{')
            lines.append(f'    label="{_escape(str(chapter["title"]))}";')
            for node in nodes_by_chapter.get(chapter_id, []):
                attrs = [f'label="{_escape(str(node["title"]))}"']
                if node["optional"]:
                    attrs.append('style="dashed"')
                lines.append(f'    "{_escape(str(node["id"]))}" [{", ".join(attrs)}];')
            lines.append("  }")
        for edge in self.edges:
            lines.append(f'  "{_escape(edge["from"])}" -> "{_escape(edge["to"])}";')
        lines.append("}")
        return "\n".join(lines)


def build_dependency_graph(project: Project) -> DependencyGraph:
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, str]] = []
    chapters: list[dict[str, object]] = []
    for chapter in project.chapters:
        chapters.append({"id": chapter.id, "title": chapter.title, "quests": len(chapter.quests)})
        for quest in chapter.quests:
            nodes.append(
                {
                    "id": quest.id,
                    "title": quest.title,
                    "chapter_id": chapter.id,
                    "optional": quest.optional,
                    "dependencies": len(quest.dependencies),
                }
            )
            for dependency in quest.dependencies:
                edges.append({"from": dependency.quest_id, "to": quest.id})
    return DependencyGraph(
        nodes=tuple(sorted(nodes, key=lambda node: str(node["id"]))),
        edges=tuple(sorted(edges, key=lambda edge: (edge["from"], edge["to"]))),
        chapters=tuple(chapters),
    )


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
