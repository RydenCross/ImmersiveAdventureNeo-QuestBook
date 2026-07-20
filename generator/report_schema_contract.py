from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from generator.audit_registry_contract import AUDIT_REGISTRY

DEFAULT_REPORT_DIRECTORY = Path("reports")
ALLOWED_STATUSES = frozenset({"pass", "fail"})


@dataclass(frozen=True, slots=True)
class ReportSchemaContract:
    checked_reports: int
    missing_reports: tuple[str, ...]
    invalid_json: tuple[str, ...]
    non_object_reports: tuple[str, ...]
    missing_status: tuple[str, ...]
    invalid_status: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_reports,
                self.invalid_json,
                self.non_object_reports,
                self.missing_status,
                self.invalid_status,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "checked_reports": self.checked_reports,
            "missing_reports": list(self.missing_reports),
            "invalid_json": list(self.invalid_json),
            "non_object_reports": list(self.non_object_reports),
            "missing_status": list(self.missing_status),
            "invalid_status": list(self.invalid_status),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report schema contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checked reports: {self.checked_reports}.",
            f"Missing reports: {len(self.missing_reports)}.",
            f"Invalid JSON reports: {len(self.invalid_json)}.",
            f"Non-object reports: {len(self.non_object_reports)}.",
            f"Reports without status: {len(self.missing_status)}.",
            f"Reports with invalid status: {len(self.invalid_status)}.",
        ]
        for label, values in (
            ("Missing", self.missing_reports),
            ("Invalid JSON", self.invalid_json),
            ("Non-object", self.non_object_reports),
            ("Missing status", self.missing_status),
            ("Invalid status", self.invalid_status),
        ):
            lines.extend(f"{label}: {name}" for name in values)
        return "\n".join(lines)


def run_report_schema_contract(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
) -> ReportSchemaContract:
    report_names = tuple(sorted(item.report for item in AUDIT_REGISTRY if item.report))
    missing: list[str] = []
    invalid_json: list[str] = []
    non_object: list[str] = []
    missing_status: list[str] = []
    invalid_status: list[str] = []

    for name in report_names:
        path = report_directory / name
        if not path.is_file():
            missing.append(name)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            invalid_json.append(name)
            continue
        if not isinstance(payload, dict):
            non_object.append(name)
            continue
        if "status" not in payload:
            missing_status.append(name)
        elif payload["status"] not in ALLOWED_STATUSES:
            invalid_status.append(name)

    return ReportSchemaContract(
        checked_reports=len(report_names),
        missing_reports=tuple(missing),
        invalid_json=tuple(invalid_json),
        non_object_reports=tuple(non_object),
        missing_status=tuple(missing_status),
        invalid_status=tuple(invalid_status),
    )
