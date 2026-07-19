from generator.github_release_contract import run_github_release_contract


def test_github_release_contract() -> None:
    result = run_github_release_contract()
    assert result.is_clean, result.to_dict()
