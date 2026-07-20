from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.report_refresh import refresh_reports


@dataclass(frozen=True, slots=True)
class ReportRefreshIdempotenceContract:
    first_refresh_clean: bool
    second_refresh_clean: bool
    second_refresh_passes: int
    files_unchanged: tuple[str, ...]
    files_changed: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            self.first_refresh_clean
            and self.second_refresh_clean
            and self.second_refresh_passes == 1
            and not self.files_changed
            and bool(self.files_unchanged)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "first_refresh_clean": self.first_refresh_clean,
            "second_refresh_clean": self.second_refresh_clean,
            "second_refresh_passes": self.second_refresh_passes,
            "files_unchanged": list(self.files_unchanged),
            "files_changed": list(self.files_changed),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Report refresh idempotence contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"First refresh clean: {'yes' if self.first_refresh_clean else 'no'}.",
            f"Second refresh clean: {'yes' if self.second_refresh_clean else 'no'}.",
            f"Second refresh passes: {self.second_refresh_passes}.",
            f"Files unchanged: {len(self.files_unchanged)}.",
            f"Files changed: {len(self.files_changed)}.",
        ))


def run_report_refresh_idempotence_contract() -> ReportRefreshIdempotenceContract:
    renderers = {
        "alpha.json": lambda: '{"status":"pass","value":1}',
        "beta.json": lambda: '{"status":"pass","value":2}',
    }
    with TemporaryDirectory(prefix="report-refresh-idempotence-") as directory:
        target = Path(directory)
        first = refresh_reports(target, renderers=renderers)
        before = {
            name: (target / name).read_bytes()
            for name in renderers
            if (target / name).is_file()
        }
        second = refresh_reports(target, renderers=renderers)
        after = {
            name: (target / name).read_bytes()
            for name in renderers
            if (target / name).is_file()
        }

    unchanged = tuple(sorted(name for name in before if before.get(name) == after.get(name)))
    changed = tuple(sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name)))
    return ReportRefreshIdempotenceContract(
        first_refresh_clean=first.is_clean,
        second_refresh_clean=second.is_clean,
        second_refresh_passes=second.passes,
        files_unchanged=unchanged,
        files_changed=changed,
    )
