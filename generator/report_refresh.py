from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Mapping, Sequence

from generator.output_writer import atomic_write_text

DEFAULT_REPORT_DIRECTORY = Path("reports")
DEFAULT_MAX_PASSES = 4


@dataclass(frozen=True, slots=True)
class ReportRefresh:
    requested_reports: int
    refreshed_reports: tuple[str, ...]
    failed_reports: tuple[str, ...]
    passes: int
    converged: bool
    changed_reports_last_pass: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.converged
            and not self.failed_reports
            and len(self.refreshed_reports) == self.requested_reports
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "requested_reports": self.requested_reports,
            "refreshed_reports": list(self.refreshed_reports),
            "failed_reports": list(self.failed_reports),
            "passes": self.passes,
            "converged": self.converged,
            "changed_reports_last_pass": list(self.changed_reports_last_pass),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report refresh: {'PASS' if self.is_clean else 'FAIL'}",
            f"Requested reports: {self.requested_reports}.",
            f"Refreshed reports: {len(self.refreshed_reports)}.",
            f"Failed reports: {len(self.failed_reports)}.",
            f"Passes: {self.passes}.",
            f"Converged: {'yes' if self.converged else 'no'}.",
        ]
        lines.extend(f"Failed: {name}" for name in self.failed_reports)
        lines.extend(f"Still changing: {name}" for name in self.changed_reports_last_pass)
        return "\n".join(lines)


def refresh_reports(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
    *,
    renderers: Mapping[str, Callable[[], str]] | None = None,
    order: Sequence[str] | None = None,
    max_passes: int = DEFAULT_MAX_PASSES,
) -> ReportRefresh:
    if max_passes < 1:
        raise ValueError("max_passes must be at least 1")
    if renderers is None:
        from generator.report_freshness import _default_renderers

        renderers = _default_renderers()
    selected_order = tuple(order) if order is not None else tuple(renderers)
    report_directory.mkdir(parents=True, exist_ok=True)
    refreshed: list[str] = []
    failed: list[str] = []
    changed_last_pass: tuple[str, ...] = ()

    for pass_number in range(1, max_passes + 1):
        changed: list[str] = []
        failed_this_pass: list[str] = []
        for name in selected_order:
            renderer = renderers.get(name)
            if renderer is None:
                failed_this_pass.append(name)
                continue
            try:
                rendered = renderer()
                json.loads(rendered)
                normalized = rendered.rstrip() + "\n"
                path = report_directory / name
                existing = path.read_text(encoding="utf-8") if path.is_file() else None
                if existing != normalized:
                    atomic_write_text(path, normalized)
                    changed.append(name)
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                failed_this_pass.append(name)
                continue
            if name not in refreshed:
                refreshed.append(name)
        failed = failed_this_pass
        changed_last_pass = tuple(changed)
        if failed:
            return ReportRefresh(
                requested_reports=len(selected_order),
                refreshed_reports=tuple(refreshed),
                failed_reports=tuple(failed),
                passes=pass_number,
                converged=False,
                changed_reports_last_pass=changed_last_pass,
            )
        if not changed:
            return ReportRefresh(
                requested_reports=len(selected_order),
                refreshed_reports=tuple(refreshed),
                failed_reports=(),
                passes=pass_number,
                converged=True,
                changed_reports_last_pass=(),
            )

    return ReportRefresh(
        requested_reports=len(selected_order),
        refreshed_reports=tuple(refreshed),
        failed_reports=tuple(failed),
        passes=max_passes,
        converged=False,
        changed_reports_last_pass=changed_last_pass,
    )
