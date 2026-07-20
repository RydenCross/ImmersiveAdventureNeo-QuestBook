from generator.questbook_review_contract import run_questbook_review_contract


def test_questbook_review_contract_is_clean() -> None:
    result = run_questbook_review_contract()
    assert result.is_clean
    assert result.review_generated
    assert result.reward_decisions_detected
    assert result.dangling_dependency_rejected
