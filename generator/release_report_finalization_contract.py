from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.report_refresh import refresh_reports
from generator.report_refresh_order_contract import ARCHIVE_DERIVED_REPORTS


@dataclass(frozen=True, slots=True)
class ReleaseReportFinalizationContract:
    reports: int
    archive_reports: tuple[str, ...]
    missing_archive_reports: tuple[str, ...]
    archive_reports_not_final: tuple[str, ...]
    refresh_clean: bool
    refresh_converged: bool
    final_archive_reports_stable: tuple[str, ...]
    final_archive_reports_changed: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.refresh_clean
            and self.refresh_converged
            and not self.missing_archive_reports
            and not self.archive_reports_not_final
            and not self.final_archive_reports_changed
            and self.final_archive_reports_stable == self.archive_reports
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "reports": self.reports,
            "archive_reports": list(self.archive_reports),
            "missing_archive_reports": list(self.missing_archive_reports),
            "archive_reports_not_final": list(self.archive_reports_not_final),
            "refresh_clean": self.refresh_clean,
            "refresh_converged": self.refresh_converged,
            "final_archive_reports_stable": list(self.final_archive_reports_stable),
            "final_archive_reports_changed": list(self.final_archive_reports_changed),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release report finalization contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Reports ordered: {self.reports}.",
            f"Archive-derived reports: {len(self.archive_reports)}.",
            f"Missing archive reports: {len(self.missing_archive_reports)}.",
            f"Archive reports outside final positions: {len(self.archive_reports_not_final)}.",
            f"Refresh clean: {'yes' if self.refresh_clean else 'no'}.",
            f"Refresh converged: {'yes' if self.refresh_converged else 'no'}.",
            f"Stable final archive reports: {len(self.final_archive_reports_stable)}.",
            f"Changed final archive reports: {len(self.final_archive_reports_changed)}.",
        ))


def run_release_report_finalization_contract() -> ReleaseReportFinalizationContract:
    from generator.report_freshness import report_refresh_order

    order = report_refresh_order()
    archive = tuple(name for name in order if name in ARCHIVE_DERIVED_REPORTS)
    missing = tuple(name for name in ARCHIVE_DERIVED_REPORTS if name not in order)
    tail = order[-len(ARCHIVE_DERIVED_REPORTS):]
    misplaced = tuple(name for name in archive if name not in tail)

    state = {"core": 0}
    renderers = {
        "core.json": lambda: json.dumps({"status": "pass", "value": state["core"]}),
        ARCHIVE_DERIVED_REPORTS[0]: lambda: json.dumps({"status": "pass", "core": state["core"]}),
        ARCHIVE_DERIVED_REPORTS[1]: lambda: json.dumps({"status": "pass", "core": state["core"]}),
    }
    with TemporaryDirectory(prefix="release-report-finalization-") as directory:
        target = Path(directory)
        state["core"] = 1
        first = refresh_reports(target, renderers=renderers, order=tuple(renderers))
        before = {name: (target / name).read_bytes() for name in ARCHIVE_DERIVED_REPORTS}
        second = refresh_reports(target, renderers=renderers, order=tuple(renderers))
        after = {name: (target / name).read_bytes() for name in ARCHIVE_DERIVED_REPORTS}

    stable = tuple(name for name in ARCHIVE_DERIVED_REPORTS if before[name] == after[name])
    changed = tuple(name for name in ARCHIVE_DERIVED_REPORTS if before[name] != after[name])
    return ReleaseReportFinalizationContract(
        reports=len(order),
        archive_reports=archive,
        missing_archive_reports=missing,
        archive_reports_not_final=misplaced,
        refresh_clean=first.is_clean and second.is_clean,
        refresh_converged=first.converged and second.converged,
        final_archive_reports_stable=stable,
        final_archive_reports_changed=changed,
    )
