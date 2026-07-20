from generator.editor_jobs_contract import run_editor_jobs_contract


def test_editor_jobs_contract_passes() -> None:
    result = run_editor_jobs_contract()
    assert result.is_clean
    assert result.staged_progress
    assert result.background_import
    assert result.atomic_document_replacement
    assert result.cooperative_cancellation
    assert result.failure_isolation
    assert result.job_api_routes
    assert result.visual_progress_controls
