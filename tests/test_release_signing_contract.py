from generator.release_signing_contract import run_release_signing_contract


def test_release_signing_contract_is_clean() -> None:
    assert run_release_signing_contract().is_clean
