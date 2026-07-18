from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass(frozen=True, slots=True)
class AuditRegistration:
    gate_name: str
    command: str
    report: str | None


AUDIT_REGISTRY = (
    AuditRegistration("release guard", "release-guard", "release-guard.json"),
    AuditRegistration("dependency audit", "dependency-audit", "dependency-audit.json"),
    AuditRegistration("progression guard", "progression-guard", "progression-guard.json"),
    AuditRegistration("identity guard", "identity-guard", "identity-guard.json"),
    AuditRegistration("contract guard", "contract-guard", "contract-guard.json"),
    AuditRegistration("reward audit", "reward-audit", "reward-audit.json"),
    AuditRegistration("task audit", "task-audit", "task-audit.json"),
    AuditRegistration("chapter audit", "chapter-audit", "chapter-audit.json"),
    AuditRegistration("text audit", "text-audit", "text-audit.json"),
    AuditRegistration("determinism audit", "determinism-audit", "determinism-audit.json"),
    AuditRegistration(
        "output manifest guard", "output-manifest-guard", "output-manifest-guard.json"
    ),
    AuditRegistration("report freshness guard", "report-freshness-guard", None),
    AuditRegistration("packaging audit", "packaging-audit", "packaging-audit.json"),
    AuditRegistration("CLI contract audit", "cli-audit", "cli-audit.json"),
    AuditRegistration(
        "documentation contract audit", "documentation-audit", "documentation-audit.json"
    ),
    AuditRegistration(
        "repository hygiene audit", "repository-hygiene-audit", "repository-hygiene-audit.json"
    ),
    AuditRegistration(
        "release artifact audit", "release-artifact-audit", "release-artifact-audit.json"
    ),
    AuditRegistration(
        "release reproducibility audit",
        "release-reproducibility-audit",
        "release-reproducibility-audit.json",
    ),
    AuditRegistration(
        "audit registry contract", "audit-registry-audit", "audit-registry-audit.json"
    ),
    AuditRegistration(
        "test inventory contract", "test-inventory-audit", "test-inventory-audit.json"
    ),
    AuditRegistration("report schema contract", "report-schema-audit", "report-schema-audit.json"),
    AuditRegistration(
        "report consistency contract", "report-consistency-audit", "report-consistency-audit.json"
    ),
    AuditRegistration(
        "report provenance contract", "report-provenance-audit", "report-provenance-audit.json"
    ),
    AuditRegistration(
        "report determinism contract", "report-determinism-audit", "report-determinism-audit.json"
    ),
    AuditRegistration("CLI output contract", "cli-output-audit", "cli-output-audit.json"),
    AuditRegistration("CLI exit-code contract", "cli-exit-code-audit", "cli-exit-code-audit.json"),
    AuditRegistration("report write-safety contract", "report-write-safety-audit", "report-write-safety-audit.json"),
    AuditRegistration("report refresh order contract", "report-refresh-order-audit", "report-refresh-order-audit.json"),
    AuditRegistration("report refresh contract", "report-refresh-audit", "report-refresh-audit.json"),
    AuditRegistration("report refresh convergence contract", "report-refresh-convergence-audit", "report-refresh-convergence-audit.json"),
    AuditRegistration("report refresh idempotence contract", "report-refresh-idempotence-audit", "report-refresh-idempotence-audit.json"),
    AuditRegistration("report refresh cache contract", "report-refresh-cache-audit", "report-refresh-cache-audit.json"),
    AuditRegistration("release report finalization contract", "release-report-finalization-audit", "release-report-finalization-audit.json"),
    AuditRegistration("release package verification contract", "release-package-verification-audit", "release-package-verification-audit.json"),
    AuditRegistration("release manifest contract", "release-manifest-audit", "release-manifest-audit.json"),
    AuditRegistration("release archive metadata contract", "release-archive-metadata-audit", "release-archive-metadata-audit.json"),
    AuditRegistration("release archive extraction safety contract", "release-archive-extraction-safety-audit", "release-archive-extraction-safety-audit.json"),
    AuditRegistration("release archive Unicode path contract", "release-archive-unicode-path-audit", "release-archive-unicode-path-audit.json"),
    AuditRegistration("release archive compression contract", "release-archive-compression-audit", "release-archive-compression-audit.json"),
    AuditRegistration("mod compatibility contract", "mod-compatibility-audit", "mod-compatibility-audit.json"),
    AuditRegistration("modpack scanner contract", "modpack-scanner-audit", "modpack-scanner-audit.json"),
    AuditRegistration("modpack content scanner contract", "modpack-content-scanner-audit", "modpack-content-scanner-audit.json"),
    AuditRegistration("progression planner contract", "progression-planner-audit", "progression-planner-audit.json"),
    AuditRegistration("quest description contract", "quest-description-audit", "quest-description-audit.json"),
    AuditRegistration("FTB blueprint exporter contract", "ftb-blueprint-exporter-audit", "ftb-blueprint-exporter-audit.json"),
    AuditRegistration("questbook review contract", "questbook-review-audit", "questbook-review-audit.json"),
    AuditRegistration("reward planner contract", "reward-planner-audit", "reward-planner-audit.json"),
    AuditRegistration("visual editor data model contract", "editor-model-audit", "editor-model-audit.json"),
    AuditRegistration("local visual editor service contract", "editor-service-audit", "editor-service-audit.json"),
    AuditRegistration("interactive visual editor UI contract", "editor-ui-audit", "editor-ui-audit.json"),
    AuditRegistration("editor workspace tools contract", "editor-workspace-audit", "editor-workspace-audit.json"),
    AuditRegistration("editor autosave and recovery contract", "editor-recovery-audit", "editor-recovery-audit.json"),
    AuditRegistration("editor background jobs contract", "editor-jobs-audit", "editor-jobs-audit.json"),
    AuditRegistration("audit performance contract", "audit-performance-audit", "audit-performance-audit.json"),
    AuditRegistration("audit dependency contract", "audit-dependency-audit", "audit-dependency-audit.json"),
)


@dataclass(frozen=True, slots=True)
class AuditRegistryContract:
    registrations: int
    missing_gate_checks: tuple[str, ...]
    unexpected_gate_checks: tuple[str, ...]
    missing_commands: tuple[str, ...]
    missing_reports: tuple[str, ...]
    duplicate_gate_names: tuple[str, ...]
    duplicate_commands: tuple[str, ...]
    duplicate_reports: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_gate_checks,
                self.unexpected_gate_checks,
                self.missing_commands,
                self.missing_reports,
                self.duplicate_gate_names,
                self.duplicate_commands,
                self.duplicate_reports,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "registrations": self.registrations,
            "missing_gate_checks": list(self.missing_gate_checks),
            "unexpected_gate_checks": list(self.unexpected_gate_checks),
            "missing_commands": list(self.missing_commands),
            "missing_reports": list(self.missing_reports),
            "duplicate_gate_names": list(self.duplicate_gate_names),
            "duplicate_commands": list(self.duplicate_commands),
            "duplicate_reports": list(self.duplicate_reports),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Audit registry contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Registrations: {self.registrations}.",
            f"Missing gate checks: {len(self.missing_gate_checks)}.",
            f"Unexpected gate checks: {len(self.unexpected_gate_checks)}.",
            f"Missing commands: {len(self.missing_commands)}.",
            f"Missing reports: {len(self.missing_reports)}.",
            f"Duplicate identifiers: {len(self.duplicate_gate_names) + len(self.duplicate_commands) + len(self.duplicate_reports)}.",
        ]
        for label, values in (
            ("Missing gate", self.missing_gate_checks),
            ("Unexpected gate", self.unexpected_gate_checks),
            ("Missing command", self.missing_commands),
            ("Missing report", self.missing_reports),
            ("Duplicate gate", self.duplicate_gate_names),
            ("Duplicate command", self.duplicate_commands),
            ("Duplicate report", self.duplicate_reports),
        ):
            lines.extend(f"{label}: {value}" for value in values)
        return "\n".join(lines)


def _duplicates(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if values.count(value) > 1}))


def run_audit_registry_contract() -> AuditRegistryContract:
    # Lazy imports avoid cycles while the CLI and quality gate register this audit.
    from generator.cli import create_parser
    from generator.cli_audit import _command_parsers
    from generator.quality_gate import _default_checks
    from generator.report_freshness import _default_renderers

    gate_names = tuple(_default_checks())
    commands = set(_command_parsers(create_parser())[0])
    reports = set(_default_renderers())
    registered_gates = tuple(item.gate_name for item in AUDIT_REGISTRY)
    registered_commands = tuple(item.command for item in AUDIT_REGISTRY)
    registered_reports = tuple(item.report for item in AUDIT_REGISTRY if item.report)

    return AuditRegistryContract(
        registrations=len(AUDIT_REGISTRY),
        missing_gate_checks=tuple(sorted(set(registered_gates) - set(gate_names))),
        unexpected_gate_checks=tuple(sorted(set(gate_names) - set(registered_gates))),
        missing_commands=tuple(sorted(set(registered_commands) - commands)),
        missing_reports=tuple(sorted(set(registered_reports) - reports)),
        duplicate_gate_names=_duplicates(registered_gates),
        duplicate_commands=_duplicates(registered_commands),
        duplicate_reports=_duplicates(registered_reports),
    )
