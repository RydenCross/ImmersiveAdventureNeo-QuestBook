from generator.release_attestation_contract import run_release_attestation_contract

def test_release_attestation_contract_is_clean() -> None:
    assert run_release_attestation_contract().is_clean


def test_release_workflow_binds_provenance_to_verified_tag_source() -> None:
    workflow = __import__("pathlib").Path(".github/workflows/publish-release.yml").read_text(encoding="utf-8")
    assert 'RELEASE_SOURCE_SHA="$(git rev-parse HEAD)"' in workflow
    assert '--revision "$RELEASE_SOURCE_SHA"' in workflow
    assert '${{ github.sha }}' not in workflow
