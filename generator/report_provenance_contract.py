from __future__ import annotations

from dataclasses import dataclass
import json

from generator.audit_registry_contract import AUDIT_REGISTRY


@dataclass(frozen=True, slots=True)
class ReportProvenanceContract:
    tracked_reports: int
    provenance: tuple[tuple[str, str], ...]
    missing_commands: tuple[str, ...]
    missing_renderers: tuple[str, ...]
    orphan_renderers: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_commands, self.missing_renderers, self.orphan_renderers))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "tracked_reports": self.tracked_reports,
            "provenance": [
                {"report": report, "command": command} for report, command in self.provenance
            ],
            "missing_commands": list(self.missing_commands),
            "missing_renderers": list(self.missing_renderers),
            "orphan_renderers": list(self.orphan_renderers),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report provenance contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Tracked reports: {self.tracked_reports}.",
            f"Missing commands: {len(self.missing_commands)}.",
            f"Missing renderers: {len(self.missing_renderers)}.",
            f"Orphan renderers: {len(self.orphan_renderers)}.",
        ]
        lines.extend(
            f"{report}: python -m generator {command}" for report, command in self.provenance
        )
        lines.extend(f"Missing command: {name}" for name in self.missing_commands)
        lines.extend(f"Missing renderer: {name}" for name in self.missing_renderers)
        lines.extend(f"Orphan renderer: {name}" for name in self.orphan_renderers)
        return "\n".join(lines)


def run_report_provenance_contract() -> ReportProvenanceContract:
    from generator.cli import create_parser
    from generator.cli_audit import _command_parsers
    from generator.report_freshness import _default_renderers

    commands = set(_command_parsers(create_parser())[0])
    renderers = set(_default_renderers())
    registrations = tuple(item for item in AUDIT_REGISTRY if item.report)
    provenance = tuple(sorted((item.report, item.command) for item in registrations))
    registered_reports = {item.report for item in registrations}

    return ReportProvenanceContract(
        tracked_reports=len(provenance),
        provenance=provenance,
        missing_commands=tuple(
            sorted(item.command for item in registrations if item.command not in commands)
        ),
        missing_renderers=tuple(sorted(registered_reports - renderers)),
        orphan_renderers=tuple(
            sorted(renderers - registered_reports - {"progression-metrics.json"})
        ),
    )
