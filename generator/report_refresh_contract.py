from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.report_refresh import refresh_reports


@dataclass(frozen=True, slots=True)
class ReportRefreshContract:
    ordered_reports: int
    renderer_reports: int
    missing_renderers: tuple[str, ...]
    unexpected_renderers: tuple[str, ...]
    probe_refreshed: tuple[str, ...]
    probe_failed: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_renderers, self.unexpected_renderers, self.probe_failed)) and len(self.probe_refreshed) == 2

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "ordered_reports": self.ordered_reports,
            "renderer_reports": self.renderer_reports,
            "missing_renderers": list(self.missing_renderers),
            "unexpected_renderers": list(self.unexpected_renderers),
            "probe_refreshed": list(self.probe_refreshed),
            "probe_failed": list(self.probe_failed),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Report refresh contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Ordered reports: {self.ordered_reports}.",
                f"Renderer reports: {self.renderer_reports}.",
                f"Missing renderers: {len(self.missing_renderers)}.",
                f"Unexpected renderers: {len(self.unexpected_renderers)}.",
                f"Probe failures: {len(self.probe_failed)}.",
            )
        )


def run_report_refresh_contract() -> ReportRefreshContract:
    from generator.report_freshness import _default_renderers, report_refresh_order

    renderers = _default_renderers()
    order = report_refresh_order()
    probe = {
        "first.json": lambda: '{"status": "pass", "value": 1}',
        "second.json": lambda: '{"status": "pass", "value": 2}',
    }
    with TemporaryDirectory() as directory:
        result = refresh_reports(Path(directory), renderers=probe, order=tuple(probe))
    return ReportRefreshContract(
        ordered_reports=len(order),
        renderer_reports=len(renderers),
        missing_renderers=tuple(sorted(set(order) - set(renderers))),
        unexpected_renderers=tuple(sorted(set(renderers) - set(order))),
        probe_refreshed=result.refreshed_reports,
        probe_failed=result.failed_reports,
    )
