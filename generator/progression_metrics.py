from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from model.project import Project


@dataclass(frozen=True, slots=True)
class ProgressionMetricsReport:
    chapters: int
    quests: int
    dependencies: int
    maximum_depth: int
    deepest_quests: tuple[str, ...]
    bottlenecks: tuple[dict[str, object], ...]
    chapter_transitions: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            "Progression metrics",
            f"Graph: {self.chapters} chapter(s), {self.quests} quest(s), "
            f"{self.dependencies} dependency edge(s).",
            f"Critical path depth: {self.maximum_depth} quest(s).",
            "Deepest quest(s): " + ", ".join(self.deepest_quests),
            f"Bottlenecks: {len(self.bottlenecks)} quest(s) with at least 4 direct dependants.",
            f"Cross-chapter transitions: {len(self.chapter_transitions)} route(s).",
        ]
        for item in self.bottlenecks:
            lines.append(
                f"Bottleneck: {item['quest_id']} ({item['title']}) -> "
                f"{item['dependants']} direct dependant(s)"
            )
        return "\n".join(lines)


def analyze_progression(project: Project) -> ProgressionMetricsReport:
    quests = {quest.id: quest for quest in project.quests}
    quest_chapter = {
        quest.id: chapter.id for chapter in project.chapters for quest in chapter.quests
    }
    outgoing: dict[str, set[str]] = {quest_id: set() for quest_id in quests}
    incoming: dict[str, set[str]] = {quest_id: set() for quest_id in quests}
    transition_counts: dict[tuple[str, str], int] = {}

    for quest in project.quests:
        for dependency in quest.dependencies:
            parent = dependency.quest_id
            if parent not in quests:
                continue
            outgoing[parent].add(quest.id)
            incoming[quest.id].add(parent)
            source = quest_chapter[parent]
            target = quest_chapter[quest.id]
            if source != target:
                transition_counts[(source, target)] = transition_counts.get((source, target), 0) + 1

    depths = _longest_depths(incoming, outgoing)
    maximum_depth = max(depths.values(), default=0)
    deepest = tuple(sorted(quest_id for quest_id, depth in depths.items() if depth == maximum_depth))

    bottlenecks = tuple(
        {
            "quest_id": quest_id,
            "title": quests[quest_id].title,
            "chapter_id": quest_chapter[quest_id],
            "dependants": len(children),
        }
        for quest_id, children in sorted(
            outgoing.items(), key=lambda item: (-len(item[1]), item[0])
        )
        if len(children) >= 4
    )
    transitions = tuple(
        {"from_chapter": source, "to_chapter": target, "edges": count}
        for (source, target), count in sorted(transition_counts.items())
    )

    return ProgressionMetricsReport(
        chapters=len(project.chapters),
        quests=len(project.quests),
        dependencies=sum(len(quest.dependencies) for quest in project.quests),
        maximum_depth=maximum_depth,
        deepest_quests=deepest,
        bottlenecks=bottlenecks,
        chapter_transitions=transitions,
    )


def _longest_depths(
    incoming: dict[str, set[str]], outgoing: dict[str, set[str]]
) -> dict[str, int]:
    remaining = {quest_id: len(parents) for quest_id, parents in incoming.items()}
    depths = {quest_id: 1 for quest_id in incoming}
    ready = sorted(quest_id for quest_id, count in remaining.items() if count == 0)
    processed = 0

    while ready:
        quest_id = ready.pop(0)
        processed += 1
        for child in sorted(outgoing[quest_id]):
            depths[child] = max(depths[child], depths[quest_id] + 1)
            remaining[child] -= 1
            if remaining[child] == 0:
                ready.append(child)
                ready.sort()

    if processed != len(incoming):
        raise ValueError("Progression metrics require an acyclic dependency graph.")
    return depths
