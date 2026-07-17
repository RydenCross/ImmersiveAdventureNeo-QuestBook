from __future__ import annotations

import json

from content import create_project
from generator.cli import main
from generator.reward_audit import audit_rewards, run_reward_audit


def test_checked_in_rewards_pass_integrity_audit() -> None:
    result = run_reward_audit()
    assert result.is_clean
    assert result.reward_count == 49
    assert result.rewarded_quests == 49
    assert result.reward_types == {"item": 49}


def test_audit_detects_duplicate_reward_ids() -> None:
    project = create_project()
    rewards = [reward for quest in project.quests for reward in quest.rewards]
    rewards[1].id = rewards[0].id
    result = audit_rewards(project)
    assert not result.is_clean
    assert len(result.duplicate_reward_ids) == 1


def test_audit_detects_invalid_item_reward_data() -> None:
    project = create_project()
    reward = next(reward for quest in project.quests for reward in quest.rewards)
    reward.data["count"] = 0
    result = audit_rewards(project)
    assert not result.is_clean
    assert "positive integer" in result.invalid_rewards[0]


def test_rewardless_terminal_quests_are_informational() -> None:
    result = run_reward_audit()
    assert result.is_clean
    assert result.rewardless_terminal_quests


def test_cli_writes_reward_audit_report(tmp_path) -> None:
    output = tmp_path / "reward-audit.json"
    assert main(["reward-audit", "--format", "json", "--output", str(output)]) == 0
    payload = json.loads(output.read_text())
    assert payload["status"] == "pass"
    assert payload["reward_count"] == 49
