from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True, slots=True)
class ReportDeterminismContract:
    checked_reports: int
    deterministic_reports: tuple[str, ...]
    nondeterministic_reports: tuple[str, ...]
    invalid_reports: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.nondeterministic_reports, self.invalid_reports))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "checked_reports": self.checked_reports,
            "deterministic_reports": list(self.deterministic_reports),
            "nondeterministic_reports": list(self.nondeterministic_reports),
            "invalid_reports": list(self.invalid_reports),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report determinism contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Checked reports: {self.checked_reports}.",
            f"Deterministic reports: {len(self.deterministic_reports)}.",
            f"Nondeterministic reports: {len(self.nondeterministic_reports)}.",
            f"Invalid reports: {len(self.invalid_reports)}.",
        ]
        lines.extend(f"Nondeterministic: {name}" for name in self.nondeterministic_reports)
        lines.extend(f"Invalid: {name}" for name in self.invalid_reports)
        return "\n".join(lines)


def run_report_determinism_contract() -> ReportDeterminismContract:
    # Lazy import avoids a cycle because freshness also renders this contract's report.
    from generator.report_freshness import _default_renderers

    renderers = _default_renderers()
    # Rendering this report from inside itself would recurse. Its deterministic
    # serialization is covered directly by the contract's regression tests.
    renderers.pop("report-determinism-audit.json", None)

    deterministic: list[str] = []
    nondeterministic: list[str] = []
    invalid: list[str] = []
    for name, renderer in sorted(renderers.items()):
        try:
            first = json.loads(renderer())
            second = json.loads(renderer())
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            invalid.append(name)
            continue
        if first == second:
            deterministic.append(name)
        else:
            nondeterministic.append(name)

    return ReportDeterminismContract(
        checked_reports=len(renderers),
        deterministic_reports=tuple(deterministic),
        nondeterministic_reports=tuple(nondeterministic),
        invalid_reports=tuple(invalid),
    )
