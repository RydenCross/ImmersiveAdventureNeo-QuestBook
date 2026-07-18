from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.report_refresh import refresh_reports


@dataclass(frozen=True, slots=True)
class ReportRefreshConvergenceContract:
    converged_probe_passes: int
    converged_probe_clean: bool
    unstable_probe_passes: int
    unstable_probe_rejected: bool
    invalid_max_passes_rejected: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.converged_probe_clean,
            self.converged_probe_passes == 3,
            self.unstable_probe_passes == 2,
            self.unstable_probe_rejected,
            self.invalid_max_passes_rejected,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "converged_probe_passes": self.converged_probe_passes,
            "converged_probe_clean": self.converged_probe_clean,
            "unstable_probe_passes": self.unstable_probe_passes,
            "unstable_probe_rejected": self.unstable_probe_rejected,
            "invalid_max_passes_rejected": self.invalid_max_passes_rejected,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Report refresh convergence contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Converged probe passes: {self.converged_probe_passes}.",
            f"Converged probe clean: {'yes' if self.converged_probe_clean else 'no'}.",
            f"Unstable probe passes: {self.unstable_probe_passes}.",
            f"Unstable probe rejected: {'yes' if self.unstable_probe_rejected else 'no'}.",
            f"Invalid max passes rejected: {'yes' if self.invalid_max_passes_rejected else 'no'}.",
        ))


def run_report_refresh_convergence_contract() -> ReportRefreshConvergenceContract:
    with TemporaryDirectory() as directory:
        target = Path(directory)
        def dependent() -> str:
            source = target / "source.json"
            value = json.loads(source.read_text(encoding="utf-8"))["value"] if source.is_file() else 0
            return json.dumps({"status": "pass", "value": value})
        renderers = {
            "dependent.json": dependent,
            "source.json": lambda: '{"status":"pass","value":1}',
        }
        converged = refresh_reports(target, renderers=renderers, order=tuple(renderers), max_passes=4)

    counter = {"value": 0}
    def unstable() -> str:
        counter["value"] += 1
        return json.dumps({"status": "pass", "value": counter["value"]})
    with TemporaryDirectory() as directory:
        unstable_result = refresh_reports(
            Path(directory), renderers={"unstable.json": unstable}, max_passes=2
        )

    invalid_rejected = False
    try:
        refresh_reports(Path("reports"), renderers={}, max_passes=0)
    except ValueError:
        invalid_rejected = True

    return ReportRefreshConvergenceContract(
        converged_probe_passes=converged.passes,
        converged_probe_clean=converged.is_clean,
        unstable_probe_passes=unstable_result.passes,
        unstable_probe_rejected=not unstable_result.is_clean and not unstable_result.converged,
        invalid_max_passes_rejected=invalid_rejected,
    )
