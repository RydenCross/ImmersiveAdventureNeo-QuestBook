from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.report_refresh import refresh_reports
from generator.report_refresh_cache import default_fingerprints


@dataclass(frozen=True, slots=True)
class ReportRefreshCacheContract:
    first_rendered_reports: int
    second_cache_hits: int
    selective_rendered_reports: tuple[str, ...]
    selective_skipped_reports: tuple[str, ...]
    tampered_report_rebuilt: bool
    corrupt_cache_rebuilt: bool
    default_reports_covered: int
    missing_default_fingerprints: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.first_rendered_reports == 2
            and self.second_cache_hits == 2
            and self.selective_rendered_reports == ("a.json",)
            and "b.json" in self.selective_skipped_reports
            and self.tampered_report_rebuilt
            and self.corrupt_cache_rebuilt
            and not self.missing_default_fingerprints
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "first_rendered_reports": self.first_rendered_reports,
            "second_cache_hits": self.second_cache_hits,
            "selective_rendered_reports": list(self.selective_rendered_reports),
            "selective_skipped_reports": list(self.selective_skipped_reports),
            "tampered_report_rebuilt": self.tampered_report_rebuilt,
            "corrupt_cache_rebuilt": self.corrupt_cache_rebuilt,
            "default_reports_covered": self.default_reports_covered,
            "missing_default_fingerprints": list(self.missing_default_fingerprints),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Report refresh cache contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Initial renderers executed: {self.first_rendered_reports}.",
                f"Second-run cache hits: {self.second_cache_hits}.",
                f"Selectively rerendered reports: {len(self.selective_rendered_reports)}.",
                f"Selectively skipped reports: {len(self.selective_skipped_reports)}.",
                f"Tampered report rebuilt: {self.tampered_report_rebuilt}.",
                f"Corrupt cache rebuilt: {self.corrupt_cache_rebuilt}.",
                f"Default reports covered: {self.default_reports_covered}.",
                f"Missing default fingerprints: {len(self.missing_default_fingerprints)}.",
            )
        )


def run_report_refresh_cache_contract() -> ReportRefreshCacheContract:
    state = {"a": 1, "b": 1}
    executions = {"a.json": 0, "b.json": 0}

    def render(name: str) -> str:
        executions[f"{name}.json"] += 1
        return json.dumps({"status": "pass", "name": name, "value": state[name]})

    with TemporaryDirectory(prefix="report-refresh-cache-") as directory:
        root = Path(directory)
        reports = root / "reports"
        cache = reports / ".report-refresh-cache.json"
        renderers = {
            "a.json": lambda: render("a"),
            "b.json": lambda: render("b"),
        }
        fingerprints = {
            "a.json": lambda: f"a:{state['a']}",
            "b.json": lambda: f"b:{state['b']}",
        }
        first = refresh_reports(
            reports,
            renderers=renderers,
            incremental=True,
            cache_path=cache,
            fingerprints=fingerprints,
        )
        second = refresh_reports(
            reports,
            renderers=renderers,
            incremental=True,
            cache_path=cache,
            fingerprints=fingerprints,
        )

        state["a"] = 2
        selective = refresh_reports(
            reports,
            renderers=renderers,
            incremental=True,
            cache_path=cache,
            fingerprints=fingerprints,
        )

        before_tamper = executions["b.json"]
        (reports / "b.json").write_text('{"status":"pass","name":"b","value":999}\n')
        refresh_reports(
            reports,
            renderers=renderers,
            incremental=True,
            cache_path=cache,
            fingerprints=fingerprints,
        )
        tampered_rebuilt = executions["b.json"] == before_tamper + 1

        cache.write_text("not json", encoding="utf-8")
        before_corrupt = sum(executions.values())
        corrupt = refresh_reports(
            reports,
            renderers=renderers,
            incremental=True,
            cache_path=cache,
            fingerprints=fingerprints,
        )
        corrupt_rebuilt = sum(executions.values()) == before_corrupt + 2 and corrupt.cache_rebuilt

    from generator.report_freshness import _default_renderers

    report_names = tuple(_default_renderers())
    defaults = default_fingerprints(
        report_names,
        root=Path("."),
        report_directory=Path("reports"),
        cache_path=Path("reports") / ".report-refresh-cache.json",
    )
    missing = tuple(sorted(set(report_names) - set(defaults)))

    return ReportRefreshCacheContract(
        first_rendered_reports=len(first.rendered_reports),
        second_cache_hits=second.cache_hits,
        selective_rendered_reports=selective.rendered_reports,
        selective_skipped_reports=selective.skipped_reports,
        tampered_report_rebuilt=tampered_rebuilt,
        corrupt_cache_rebuilt=corrupt_rebuilt,
        default_reports_covered=len(defaults),
        missing_default_fingerprints=missing,
    )
