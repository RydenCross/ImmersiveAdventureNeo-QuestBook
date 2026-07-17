from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


COUNT_FIELDS = (
    "chapters",
    "quests",
    "optional_quests",
    "generated_chapters",
    "generated_quests",
    "validation_errors",
    "validation_warnings",
    "empty_descriptions",
    "taskless_quests",
    "duplicate_titles",
    "manifest_references",
    "manifest_unique_items",
    "manifest_namespaces",
)

QUALITY_FIELDS = (
    "validation_errors",
    "validation_warnings",
    "empty_descriptions",
    "taskless_quests",
    "duplicate_titles",
)

CONTENT_FIELDS = (
    "chapters",
    "quests",
    "optional_quests",
    "generated_chapters",
    "generated_quests",
    "manifest_references",
    "manifest_unique_items",
    "manifest_namespaces",
)


@dataclass(frozen=True, slots=True)
class ReleaseComparison:
    baseline: dict[str, Any]
    current: dict[str, Any]
    deltas: dict[str, int]
    regressions: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.regressions

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "is_clean": self.is_clean,
            "baseline": self.baseline,
            "current": self.current,
            "deltas": self.deltas,
            "regressions": list(self.regressions),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        status = "PASS" if self.is_clean else "FAIL"
        changed = [
            f"  {field}: {self.baseline[field]} -> {self.current[field]} "
            f"({self.deltas[field]:+d})"
            for field in COUNT_FIELDS
            if self.deltas[field]
        ]
        lines = [f"Release comparison: {status}"]
        lines.append("Changes:" if changed else "Changes: none")
        lines.extend(changed)
        if self.regressions:
            lines.append("Regressions:")
            lines.extend(f"  - {message}" for message in self.regressions)
        else:
            lines.append("Regressions: none")
        return "\n".join(lines)


def load_release_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read release report {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"Release report {path} must contain a JSON object.")

    missing = [field for field in COUNT_FIELDS if field not in payload]
    if missing:
        raise ValueError(f"Release report {path} is missing field(s): {', '.join(missing)}")

    invalid = [field for field in COUNT_FIELDS if not isinstance(payload[field], int)]
    if invalid:
        raise ValueError(f"Release report {path} has non-integer field(s): {', '.join(invalid)}")

    return payload


def compare_release_reports(baseline: dict[str, Any], current: dict[str, Any]) -> ReleaseComparison:
    deltas = {field: current[field] - baseline[field] for field in COUNT_FIELDS}
    regressions: list[str] = []

    if current.get("status") == "fail" or current.get("is_clean") is False:
        regressions.append("The current release report is not clean.")

    for field in QUALITY_FIELDS:
        if deltas[field] > 0:
            regressions.append(
                f"{field.replace('_', ' ')} increased from {baseline[field]} to {current[field]}."
            )

    for field in CONTENT_FIELDS:
        if deltas[field] < 0:
            regressions.append(
                f"{field.replace('_', ' ')} decreased from {baseline[field]} to {current[field]}."
            )

    if current["chapters"] != current["generated_chapters"]:
        regressions.append("Current authored and generated chapter totals do not match.")
    if current["quests"] != current["generated_quests"]:
        regressions.append("Current authored and generated quest totals do not match.")

    return ReleaseComparison(
        baseline=baseline,
        current=current,
        deltas=deltas,
        regressions=tuple(regressions),
    )
