import json
from pathlib import Path

import pytest

from generator.report_refresh import refresh_reports
from generator.report_refresh_convergence_contract import run_report_refresh_convergence_contract


def test_report_refresh_convergence_contract_is_clean() -> None:
    result = run_report_refresh_convergence_contract()
    assert result.is_clean
    assert result.converged_probe_passes == 3
    assert result.unstable_probe_rejected


def test_refresh_reports_reaches_fixed_point(tmp_path: Path) -> None:
    def dependent() -> str:
        source = tmp_path / "source.json"
        value = json.loads(source.read_text())["value"] if source.exists() else 0
        return json.dumps({"status": "pass", "value": value})
    result = refresh_reports(
        tmp_path,
        renderers={"dependent.json": dependent, "source.json": lambda: '{"status":"pass","value":7}'},
        order=("dependent.json", "source.json"),
    )
    assert result.is_clean
    assert result.converged
    assert result.passes == 3
    assert json.loads((tmp_path / "dependent.json").read_text())["value"] == 7


def test_refresh_reports_rejects_nonconvergence(tmp_path: Path) -> None:
    counter = {"value": 0}
    def renderer() -> str:
        counter["value"] += 1
        return json.dumps({"status": "pass", "value": counter["value"]})
    result = refresh_reports(tmp_path, renderers={"unstable.json": renderer}, max_passes=2)
    assert not result.is_clean
    assert not result.converged
    assert result.changed_reports_last_pass == ("unstable.json",)


def test_refresh_reports_rejects_invalid_pass_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        refresh_reports(tmp_path, renderers={}, max_passes=0)
