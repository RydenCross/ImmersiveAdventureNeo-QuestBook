from generator.project_bundle_contract import run_project_bundle_contract


def test_project_bundle_contract_is_clean() -> None:
    result = run_project_bundle_contract()
    assert result.is_clean
    assert result.deterministic_bundle
    assert result.safe_installation
    assert result.api_routes
