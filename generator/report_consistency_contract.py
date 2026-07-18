from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from generator.audit_registry_contract import AUDIT_REGISTRY

DEFAULT_REPORT_DIRECTORY = Path("reports")
DEFECT_PREFIXES = (
    "missing_",
    "invalid_",
    "duplicate_",
    "unexpected_",
    "stale_",
    "changed_",
    "empty_",
    "forbidden_",
    "oversized_",
    "unresolved_",
    "orphan_",
    "cycle_",
    "broken_",
    "mismatched_",
    "failed_",
)


@dataclass(frozen=True, slots=True)
class ReportConsistencyContract:
    checked_reports: int
    inconsistent_status: tuple[str, ...]
    invalid_summary_counts: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.inconsistent_status, self.invalid_summary_counts))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "checked_reports": self.checked_reports,
            "inconsistent_status": list(self.inconsistent_status),
            "invalid_summary_counts": list(self.invalid_summary_counts),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report consistency contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checked reports: {self.checked_reports}.",
            f"Inconsistent status reports: {len(self.inconsistent_status)}.",
            f"Invalid summary counts: {len(self.invalid_summary_counts)}.",
        ]
        lines.extend(f"Status mismatch: {name}" for name in self.inconsistent_status)
        lines.extend(f"Count mismatch: {name}" for name in self.invalid_summary_counts)
        return "\n".join(lines)


def _defect_lists(payload: dict[str, object]) -> list[list[object]]:
    return [
        value
        for key, value in payload.items()
        if isinstance(value, list) and key.startswith(DEFECT_PREFIXES)
    ]


def _count_mismatches(payload: dict[str, object]) -> bool:
    for key, value in payload.items():
        if not isinstance(value, int) or isinstance(value, bool):
            continue
        candidates = (key.removesuffix("_count"), key.removesuffix("s"))
        for candidate in candidates:
            listed = payload.get(candidate)
            if isinstance(listed, list) and value != len(listed):
                return True
    return False


def run_report_consistency_contract(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> ReportConsistencyContract:
    names = tuple(sorted(item.report for item in AUDIT_REGISTRY if item.report))
    inconsistent: list[str] = []
    count_mismatches: list[str] = []
    for name in names:
        path = report_directory / name
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict) or payload.get("status") not in {"pass", "fail"}:
            continue
        has_defects = any(items for items in _defect_lists(payload))
        if (payload["status"] == "pass" and has_defects) or (
            payload["status"] == "fail" and not has_defects
        ):
            inconsistent.append(name)
        if _count_mismatches(payload):
            count_mismatches.append(name)
    return ReportConsistencyContract(
        checked_reports=len(names),
        inconsistent_status=tuple(inconsistent),
        invalid_summary_counts=tuple(count_mismatches),
    )
