from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from generator.release_check import ReleaseCheckReport, run_release_check
from generator.release_compare import (
    ReleaseComparison,
    compare_release_reports,
    load_release_report,
)

DEFAULT_BASELINE_PATH = Path("reports/release-baseline.json")


@dataclass(frozen=True, slots=True)
class ReleaseGuardResult:
    release: ReleaseCheckReport
    comparison: ReleaseComparison

    @property
    def is_clean(self) -> bool:
        return self.release.is_clean and self.comparison.is_clean

    def format(self) -> str:
        status = "PASS" if self.is_clean else "FAIL"
        return "\n".join(
            (
                f"Release guard: {status}",
                self.release.format(),
                self.comparison.format(),
            )
        )

    def format_json(self) -> str:
        import json

        return json.dumps(
            {
                "status": "pass" if self.is_clean else "fail",
                "is_clean": self.is_clean,
                "release": self.release.to_dict(),
                "comparison": self.comparison.to_dict(),
            },
            indent=2,
            sort_keys=True,
        )


def run_release_guard(
    baseline_path: Path = DEFAULT_BASELINE_PATH,
    build_output: Path | None = None,
) -> ReleaseGuardResult:
    baseline = load_release_report(baseline_path)
    release = run_release_check(build_output)
    comparison = compare_release_reports(baseline, release.to_dict())
    return ReleaseGuardResult(release=release, comparison=comparison)


def refresh_release_baseline(
    destination: Path = DEFAULT_BASELINE_PATH,
    build_output: Path | None = None,
) -> ReleaseCheckReport:
    report = run_release_check(build_output)
    if not report.is_clean:
        raise ValueError("Refusing to refresh the release baseline because release-check failed.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.format_json() + "\n", encoding="utf-8")
    return report
