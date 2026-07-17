from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from model.project import Project


@dataclass(frozen=True, slots=True)
class DependencyAuditReport:
    chapters: int
    quests: int
    dependencies: int
    entry_quests: int
    terminal_quests: int
    cycles: tuple[tuple[str, ...], ...]
    unreachable_quests: tuple[str, ...]
    duplicate_dependencies: tuple[str, ...]
    chapters_without_entry: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.cycles,
                self.unreachable_quests,
                self.duplicate_dependencies,
                self.chapters_without_entry,
            )
        )

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["cycles"] = [list(cycle) for cycle in self.cycles]
        data["status"] = "pass" if self.is_clean else "fail"
        data["is_clean"] = self.is_clean
        return data

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        status = "PASS" if self.is_clean else "FAIL"
        lines = [
            f"Dependency audit: {status}",
            f"Graph: {self.chapters} chapter(s), {self.quests} quest(s), "
            f"{self.dependencies} dependency edge(s).",
            f"Progression: {self.entry_quests} entry quest(s), "
            f"{self.terminal_quests} terminal quest(s).",
            f"Problems: {len(self.cycles)} cycle(s), "
            f"{len(self.unreachable_quests)} unreachable quest(s), "
            f"{len(self.duplicate_dependencies)} duplicate dependency declaration(s), "
            f"{len(self.chapters_without_entry)} chapter(s) without an entry path.",
        ]
        for cycle in self.cycles:
            lines.append("Cycle: " + " -> ".join(cycle))
        for quest_id in self.unreachable_quests:
            lines.append(f"Unreachable quest: {quest_id}")
        for value in self.duplicate_dependencies:
            lines.append(f"Duplicate dependency: {value}")
        for chapter_id in self.chapters_without_entry:
            lines.append(f"Chapter without entry path: {chapter_id}")
        return "\n".join(lines)


def audit_dependencies(project: Project) -> DependencyAuditReport:
    quests = {quest.id: quest for quest in project.quests}
    outgoing: dict[str, set[str]] = {quest_id: set() for quest_id in quests}
    incoming: dict[str, set[str]] = {quest_id: set() for quest_id in quests}
    duplicates: list[str] = []

    for quest in project.quests:
        seen: set[str] = set()
        for dependency in quest.dependencies:
            dependency_id = dependency.quest_id
            if dependency_id in seen:
                duplicates.append(f"{quest.id} -> {dependency_id}")
            seen.add(dependency_id)
            if dependency_id in quests:
                outgoing[dependency_id].add(quest.id)
                incoming[quest.id].add(dependency_id)

    roots = sorted(quest_id for quest_id, parents in incoming.items() if not parents)
    reachable: set[str] = set()
    stack = list(reversed(roots))
    while stack:
        quest_id = stack.pop()
        if quest_id in reachable:
            continue
        reachable.add(quest_id)
        stack.extend(sorted(outgoing[quest_id], reverse=True))

    chapter_entries: dict[str, int] = {}
    for chapter in project.chapters:
        chapter_ids = {quest.id for quest in chapter.quests}
        chapter_entries[chapter.id] = sum(
            not any(parent in chapter_ids for parent in incoming[quest.id])
            for quest in chapter.quests
        )

    return DependencyAuditReport(
        chapters=len(project.chapters),
        quests=len(project.quests),
        dependencies=sum(len(quest.dependencies) for quest in project.quests),
        entry_quests=len(roots),
        terminal_quests=sum(not children for children in outgoing.values()),
        cycles=tuple(_find_cycles(incoming)),
        unreachable_quests=tuple(sorted(set(quests) - reachable)),
        duplicate_dependencies=tuple(sorted(duplicates)),
        chapters_without_entry=tuple(
            sorted(chapter_id for chapter_id, count in chapter_entries.items() if count == 0)
        ),
    )


def _find_cycles(incoming: dict[str, set[str]]) -> list[tuple[str, ...]]:
    state: dict[str, int] = {quest_id: 0 for quest_id in incoming}
    path: list[str] = []
    positions: dict[str, int] = {}
    cycles: set[tuple[str, ...]] = set()

    def visit(quest_id: str) -> None:
        state[quest_id] = 1
        positions[quest_id] = len(path)
        path.append(quest_id)
        for parent in sorted(incoming[quest_id]):
            if state[parent] == 0:
                visit(parent)
            elif state[parent] == 1:
                raw = path[positions[parent] :] + [parent]
                body = raw[:-1]
                start = min(range(len(body)), key=body.__getitem__)
                normalized = tuple(body[start:] + body[:start] + [body[start]])
                cycles.add(normalized)
        path.pop()
        positions.pop(quest_id)
        state[quest_id] = 2

    for quest_id in sorted(incoming):
        if state[quest_id] == 0:
            visit(quest_id)
    return sorted(cycles)
