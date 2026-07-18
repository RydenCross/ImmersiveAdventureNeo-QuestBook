from generator.reward_planner_contract import run_reward_planner_contract


def test_reward_planner_contract_passes() -> None:
    result = run_reward_planner_contract()
    assert result.is_clean, result.format()
