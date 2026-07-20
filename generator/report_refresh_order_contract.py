from __future__ import annotations

from dataclasses import dataclass
import json

ARCHIVE_DERIVED_REPORTS = (
    "release-artifact-audit.json",
    "release-reproducibility-audit.json",
)


@dataclass(frozen=True, slots=True)
class ReportRefreshOrderContract:
    reports: int
    archive_reports: tuple[str, ...]
    missing_archive_reports: tuple[str, ...]
    archive_reports_not_last: tuple[str, ...]
    duplicate_reports: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (self.missing_archive_reports, self.archive_reports_not_last, self.duplicate_reports)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "reports": self.reports,
            "archive_reports": list(self.archive_reports),
            "missing_archive_reports": list(self.missing_archive_reports),
            "archive_reports_not_last": list(self.archive_reports_not_last),
            "duplicate_reports": list(self.duplicate_reports),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report refresh order contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Reports ordered: {self.reports}.",
            f"Archive-derived reports: {len(self.archive_reports)}.",
            f"Missing archive reports: {len(self.missing_archive_reports)}.",
            f"Archive reports outside final positions: {len(self.archive_reports_not_last)}.",
            f"Duplicate reports: {len(self.duplicate_reports)}.",
        ]
        lines.extend(f"Missing archive report: {name}" for name in self.missing_archive_reports)
        lines.extend(f"Archive report not last: {name}" for name in self.archive_reports_not_last)
        lines.extend(f"Duplicate report: {name}" for name in self.duplicate_reports)
        return "\n".join(lines)


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def run_report_refresh_order_contract() -> ReportRefreshOrderContract:
    from generator.report_freshness import report_refresh_order

    order = report_refresh_order()
    archive = tuple(name for name in order if name in ARCHIVE_DERIVED_REPORTS)
    missing = tuple(name for name in ARCHIVE_DERIVED_REPORTS if name not in order)
    expected_tail = tuple(name for name in ARCHIVE_DERIVED_REPORTS if name in order)
    actual_tail = order[-len(expected_tail):] if expected_tail else ()
    misplaced = tuple(name for name in expected_tail if name not in actual_tail)
    return ReportRefreshOrderContract(
        reports=len(order),
        archive_reports=archive,
        missing_archive_reports=missing,
        archive_reports_not_last=misplaced,
        duplicate_reports=_duplicates(order),
    )
