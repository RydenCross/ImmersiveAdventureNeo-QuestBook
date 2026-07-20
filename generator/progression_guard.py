from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from content import create_project
from generator.progression_metrics import ProgressionMetricsReport, analyze_progression

DEFAULT_BUDGET_PATH = Path("reports/progression-budget.json")


@dataclass(frozen=True, slots=True)
class ProgressionBudget:
    minimum_quests: int
    minimum_dependencies: int
    maximum_depth: int
    maximum_bottlenecks: int
    maximum_direct_dependants: int
    maximum_chapter_transitions: int

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ProgressionBudget":
        try:
            return cls(
                minimum_quests=int(payload["minimum_quests"]),
                minimum_dependencies=int(payload["minimum_dependencies"]),
                maximum_depth=int(payload["maximum_depth"]),
                maximum_bottlenecks=int(payload["maximum_bottlenecks"]),
                maximum_direct_dependants=int(payload["maximum_direct_dependants"]),
                maximum_chapter_transitions=int(payload["maximum_chapter_transitions"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid progression budget.") from exc


@dataclass(frozen=True, slots=True)
class ProgressionGuardResult:
    metrics: ProgressionMetricsReport
    budget: ProgressionBudget
    violations: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "metrics": self.metrics.to_dict(),
            "budget": asdict(self.budget),
            "violations": list(self.violations),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        maximum_fan_out = max(
            (int(item["dependants"]) for item in self.metrics.bottlenecks), default=0
        )
        lines = [
            f"Progression guard: {'PASS' if self.is_clean else 'FAIL'}",
            f"Quests: {self.metrics.quests} / {self.budget.minimum_quests} minimum.",
            "Dependencies: "
            f"{self.metrics.dependencies} / {self.budget.minimum_dependencies} minimum.",
            f"Critical path: {self.metrics.maximum_depth} / "
            f"{self.budget.maximum_depth} maximum.",
            f"Bottlenecks: {len(self.metrics.bottlenecks)} / "
            f"{self.budget.maximum_bottlenecks} maximum.",
            f"Maximum direct dependants: {maximum_fan_out} / "
            f"{self.budget.maximum_direct_dependants} maximum.",
            f"Cross-chapter routes: {len(self.metrics.chapter_transitions)} / "
            f"{self.budget.maximum_chapter_transitions} maximum.",
        ]
        lines.extend(f"Violation: {violation}" for violation in self.violations)
        return "\n".join(lines)


def load_progression_budget(path: Path = DEFAULT_BUDGET_PATH) -> ProgressionBudget:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Progression budget not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid progression budget JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Invalid progression budget.")
    return ProgressionBudget.from_dict(payload)


def guard_progression(
    metrics: ProgressionMetricsReport, budget: ProgressionBudget
) -> ProgressionGuardResult:
    violations: list[str] = []
    maximum_fan_out = max((int(item["dependants"]) for item in metrics.bottlenecks), default=0)

    if metrics.quests < budget.minimum_quests:
        violations.append(
            f"Quest count dropped to {metrics.quests}; minimum is {budget.minimum_quests}."
        )
    if metrics.dependencies < budget.minimum_dependencies:
        violations.append(
            "Dependency count dropped to "
            f"{metrics.dependencies}; minimum is {budget.minimum_dependencies}."
        )
    if metrics.maximum_depth > budget.maximum_depth:
        violations.append(
            f"Critical path grew to {metrics.maximum_depth}; maximum is " f"{budget.maximum_depth}."
        )
    if len(metrics.bottlenecks) > budget.maximum_bottlenecks:
        violations.append(
            f"Bottleneck count grew to {len(metrics.bottlenecks)}; maximum is "
            f"{budget.maximum_bottlenecks}."
        )
    if maximum_fan_out > budget.maximum_direct_dependants:
        violations.append(
            f"Maximum direct dependants grew to {maximum_fan_out}; maximum is "
            f"{budget.maximum_direct_dependants}."
        )
    if len(metrics.chapter_transitions) > budget.maximum_chapter_transitions:
        violations.append(
            f"Cross-chapter routes grew to {len(metrics.chapter_transitions)}; maximum is "
            f"{budget.maximum_chapter_transitions}."
        )

    return ProgressionGuardResult(metrics, budget, tuple(violations))


def run_progression_guard(
    budget_path: Path = DEFAULT_BUDGET_PATH,
) -> ProgressionGuardResult:
    return guard_progression(
        analyze_progression(create_project()), load_progression_budget(budget_path)
    )
