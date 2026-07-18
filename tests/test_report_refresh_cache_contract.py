import json
from pathlib import Path

from generator.report_refresh import refresh_reports
from generator.report_refresh_cache_contract import run_report_refresh_cache_contract


def test_report_refresh_cache_contract_is_clean() -> None:
    result = run_report_refresh_cache_contract()
    assert result.is_clean
    assert result.second_cache_hits == 2
    assert result.selective_rendered_reports == ("a.json",)


def test_incremental_refresh_skips_unchanged_renderers(tmp_path: Path) -> None:
    calls = {"report.json": 0}

    def render() -> str:
        calls["report.json"] += 1
        return json.dumps({"status": "pass", "value": 1})

    cache = tmp_path / ".report-refresh-cache.json"
    fingerprints = {"report.json": lambda: "stable-input"}
    first = refresh_reports(
        tmp_path,
        renderers={"report.json": render},
        incremental=True,
        cache_path=cache,
        fingerprints=fingerprints,
    )
    second = refresh_reports(
        tmp_path,
        renderers={"report.json": render},
        incremental=True,
        cache_path=cache,
        fingerprints=fingerprints,
    )

    assert first.rendered_reports == ("report.json",)
    assert second.rendered_reports == ()
    assert second.skipped_reports == ("report.json",)
    assert calls["report.json"] == 1


def test_incremental_refresh_rebuilds_tampered_output(tmp_path: Path) -> None:
    calls = 0

    def render() -> str:
        nonlocal calls
        calls += 1
        return '{"status":"pass","value":1}'

    cache = tmp_path / ".report-refresh-cache.json"
    kwargs = {
        "renderers": {"report.json": render},
        "incremental": True,
        "cache_path": cache,
        "fingerprints": {"report.json": lambda: "stable-input"},
    }
    refresh_reports(tmp_path, **kwargs)
    (tmp_path / "report.json").write_text('{"status":"pass","value":2}\n')
    result = refresh_reports(tmp_path, **kwargs)

    assert result.rendered_reports == ("report.json",)
    assert calls == 2
    assert json.loads((tmp_path / "report.json").read_text())["value"] == 1


def test_incremental_refresh_uses_report_directory_cache_by_default(tmp_path: Path) -> None:
    result = refresh_reports(
        tmp_path,
        renderers={"report.json": lambda: '{"status":"pass"}'},
        incremental=True,
        fingerprints={"report.json": lambda: "stable-input"},
    )

    assert result.is_clean
    assert (tmp_path / ".report-refresh-cache.json").is_file()
