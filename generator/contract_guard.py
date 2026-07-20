from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from content import create_project
from model.project import Project

DEFAULT_CONTRACT_BASELINE_PATH = Path("reports/quest-contract-baseline.json")


@dataclass(frozen=True, slots=True)
class ContractManifest:
    quests: tuple[dict[str, object], ...]

    @property
    def quest_count(self) -> int:
        return len(self.quests)

    @property
    def task_count(self) -> int:
        return sum(len(item["tasks"]) for item in self.quests)

    @property
    def reward_count(self) -> int:
        return sum(len(item["rewards"]) for item in self.quests)

    def to_dict(self) -> dict[str, object]:
        return {
            "quest_count": self.quest_count,
            "task_count": self.task_count,
            "reward_count": self.reward_count,
            "quests": list(self.quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class ContractGuardResult:
    baseline: ContractManifest
    current: ContractManifest
    missing_quests: tuple[str, ...]
    changed_quests: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.missing_quests and not self.changed_quests

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "baseline": {
                "quests": self.baseline.quest_count,
                "tasks": self.baseline.task_count,
                "rewards": self.baseline.reward_count,
            },
            "current": {
                "quests": self.current.quest_count,
                "tasks": self.current.task_count,
                "rewards": self.current.reward_count,
            },
            "missing_quests": list(self.missing_quests),
            "changed_quests": list(self.changed_quests),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Quest contract guard: {'PASS' if self.is_clean else 'FAIL'}",
            f"Quests: {self.current.quest_count} current / {self.baseline.quest_count} protected.",
            f"Tasks: {self.current.task_count} current / {self.baseline.task_count} protected.",
            f"Rewards: {self.current.reward_count} current / {self.baseline.reward_count} protected.",
            f"Missing quests: {len(self.missing_quests)}.",
            f"Changed quest contracts: {len(self.changed_quests)}.",
        ]
        lines.extend(f"Missing quest: {value}" for value in self.missing_quests)
        lines.extend(f"Changed quest contract: {value}" for value in self.changed_quests)
        return "\n".join(lines)


def _task_contract(task: object) -> dict[str, object]:
    return {"id": task.id, "type": task.type.value}


def _reward_contract(reward: object) -> dict[str, object]:
    return {"id": reward.id, "type": reward.type.value}


def build_contract_manifest(project: Project) -> ContractManifest:
    quests: list[dict[str, object]] = []
    for chapter in project.chapters:
        for quest in chapter.quests:
            quests.append(
                {
                    "id": quest.id,
                    "icon": quest.icon,
                    "difficulty": quest.difficulty.value,
                    "hidden": quest.hidden,
                    "optional": quest.optional,
                    "repeatable": quest.repeatable,
                    "tasks": [_task_contract(task) for task in quest.tasks],
                    "rewards": [_reward_contract(reward) for reward in quest.rewards],
                }
            )
    return ContractManifest(tuple(sorted(quests, key=lambda item: str(item["id"]))))


def load_contract_manifest(path: Path = DEFAULT_CONTRACT_BASELINE_PATH) -> ContractManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Quest contract baseline not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid quest contract baseline JSON: {path}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("quests"), list):
        raise ValueError("Invalid quest contract baseline.")
    quests = payload["quests"]
    if not all(isinstance(item, dict) for item in quests):
        raise ValueError("Invalid quest contract baseline entries.")
    return ContractManifest(tuple(quests))


def compare_contract_manifests(
    baseline: ContractManifest, current: ContractManifest
) -> ContractGuardResult:
    baseline_quests = {str(item["id"]): item for item in baseline.quests}
    current_quests = {str(item["id"]): item for item in current.quests}
    missing = tuple(sorted(set(baseline_quests) - set(current_quests)))
    changed = tuple(
        sorted(
            quest_id
            for quest_id in set(baseline_quests) & set(current_quests)
            if baseline_quests[quest_id] != current_quests[quest_id]
        )
    )
    return ContractGuardResult(baseline, current, missing, changed)


def run_contract_guard(
    baseline_path: Path = DEFAULT_CONTRACT_BASELINE_PATH,
) -> ContractGuardResult:
    return compare_contract_manifests(
        load_contract_manifest(baseline_path), build_contract_manifest(create_project())
    )


def refresh_contract_baseline(
    destination: Path = DEFAULT_CONTRACT_BASELINE_PATH,
) -> ContractManifest:
    manifest = build_contract_manifest(create_project())
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(manifest.format_json() + "\n", encoding="utf-8")
    return manifest
