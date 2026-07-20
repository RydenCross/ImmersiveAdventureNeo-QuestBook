from generator.release_attestation_contract import run_release_attestation_contract

def test_release_attestation_contract_is_clean() -> None:
    assert run_release_attestation_contract().is_clean
