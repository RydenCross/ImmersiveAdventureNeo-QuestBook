from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Mapping, Sequence

from generator.output_writer import atomic_write_text

DEFAULT_REPORT_DIRECTORY = Path("reports")


@dataclass(frozen=True, slots=True)
class ReportRefresh:
    requested_reports: int
    refreshed_reports: tuple[str, ...]
    failed_reports: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.failed_reports and len(self.refreshed_reports) == self.requested_reports

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "requested_reports": self.requested_reports,
            "refreshed_reports": list(self.refreshed_reports),
            "failed_reports": list(self.failed_reports),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report refresh: {'PASS' if self.is_clean else 'FAIL'}",
            f"Requested reports: {self.requested_reports}.",
            f"Refreshed reports: {len(self.refreshed_reports)}.",
            f"Failed reports: {len(self.failed_reports)}.",
        ]
        lines.extend(f"Failed: {name}" for name in self.failed_reports)
        return "\n".join(lines)


def refresh_reports(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
    *,
    renderers: Mapping[str, Callable[[], str]] | None = None,
    order: Sequence[str] | None = None,
) -> ReportRefresh:
    if renderers is None:
        from generator.report_freshness import _default_renderers

        renderers = _default_renderers()
    selected_order = tuple(order) if order is not None else tuple(renderers)
    report_directory.mkdir(parents=True, exist_ok=True)
    refreshed: list[str] = []
    failed: list[str] = []
    for name in selected_order:
        renderer = renderers.get(name)
        if renderer is None:
            failed.append(name)
            continue
        try:
            rendered = renderer()
            json.loads(rendered)
            atomic_write_text(report_directory / name, rendered.rstrip() + "\n")
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            failed.append(name)
            continue
        refreshed.append(name)
    return ReportRefresh(
        requested_reports=len(selected_order),
        refreshed_reports=tuple(refreshed),
        failed_reports=tuple(failed),
    )
