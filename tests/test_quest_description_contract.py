from generator.quest_description_contract import run_quest_description_contract


def test_quest_description_contract_passes() -> None:
    result = run_quest_description_contract()
    assert result.is_clean, result.format()
