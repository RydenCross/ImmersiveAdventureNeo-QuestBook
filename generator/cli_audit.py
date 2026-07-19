from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import tomllib

DEFAULT_PYPROJECT_PATH = Path("pyproject.toml")
EXPECTED_CONSOLE_SCRIPT = "generator.cli:main"
EXPECTED_COMMANDS = (
    "audit",
    "audit-dependency-audit",
    "audit-performance-audit",
    "audit-registry-audit",
    "chapter-audit",
    "cli-audit",
    "cli-exit-code-audit",
    "cli-output-audit",
    "contract-baseline",
    "contract-guard",
    "dependency-audit",
    "dependency-graph",
    "documentation-audit",
    "determinism-audit",
    "identity-baseline",
    "identity-guard",
    "lint",
    "mod-compatibility-audit",
    "modpack-scan",
    "modpack-content-scan",
    "quest-blueprint",
    "quest-description-plan",
    "quest-reward-plan",
    "quest-editor-model",
    "quest-project-bundle",
    "quest-project-inspect",
    "quest-project-install",
    "questbook-review",
    "modpack-scanner-audit",
    "modpack-content-scanner-audit",
    "progression-planner-audit",
    "ftb-quest-export",
    "ftb-blueprint-exporter-audit",
    "questbook-review-audit",
    "reward-planner-audit",
    "quest-description-audit",
    "editor-model-audit",
    "editor-service-audit",
    "editor-ui-audit",
    "editor-workspace-audit",
    "editor-recovery-audit",
    "editor-jobs-audit",
    "project-bundle-audit",
    "quest-editor-serve",
    "output-manifest",
    "output-manifest-guard",
    "packaging-audit",
    "progression-guard",
    "progression-metrics",
    "quality-gate",
    "registry-audit",
    "registry-manifest",
    "release-artifact-audit",
    "release-reproducibility-audit",
    "release-baseline",
    "release-check",
    "release-compare",
    "release-guard",
    "report-freshness-guard",
    "report-consistency-audit",
    "report-determinism-audit",
    "report-provenance-audit",
    "report-refresh",
    "report-refresh-audit",
    "report-refresh-cache-audit",
    "report-refresh-convergence-audit",
    "report-refresh-idempotence-audit",
    "release-report-finalization-audit",
    "release-package-verification-audit",
    "release-manifest-audit",
    "release-archive-metadata-audit",
    "release-archive-extraction-safety-audit",
    "release-archive-unicode-path-audit",
    "release-archive-compression-audit",
    "report-refresh-order-audit",
    "report-write-safety-audit",
    "report-schema-audit",
    "repository-hygiene-audit",
    "reward-audit",
    "task-audit",
    "test-inventory-audit",
    "text-audit",
)


@dataclass(frozen=True, slots=True)
class CliAudit:
    commands: tuple[str, ...]
    missing_commands: tuple[str, ...]
    undocumented_commands: tuple[str, ...]
    commands_without_help: tuple[str, ...]
    console_script: str | None
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_commands,
                self.undocumented_commands,
                self.commands_without_help,
                self.errors,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "command_count": len(self.commands),
            "commands": list(self.commands),
            "missing_commands": list(self.missing_commands),
            "undocumented_commands": list(self.undocumented_commands),
            "commands_without_help": list(self.commands_without_help),
            "console_script": self.console_script,
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"CLI contract audit: {'PASS' if self.is_clean else 'FAIL'}",
            f"Commands: {len(self.commands)}.",
            f"Missing commands: {len(self.missing_commands)}.",
            f"Unexpected commands: {len(self.undocumented_commands)}.",
            f"Commands without help: {len(self.commands_without_help)}.",
            f"Console script: {self.console_script or '<missing>'}.",
            f"Errors: {len(self.errors)}.",
        ]
        lines.extend(f"Missing: {name}" for name in self.missing_commands)
        lines.extend(f"Unexpected: {name}" for name in self.undocumented_commands)
        lines.extend(f"No help: {name}" for name in self.commands_without_help)
        lines.extend(f"Error: {error}" for error in self.errors)
        return "\n".join(lines)


def _command_parsers(
    parser: argparse.ArgumentParser,
) -> tuple[dict[str, argparse.ArgumentParser], dict[str, str | None]]:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            help_text = {choice.dest: choice.help for choice in action._choices_actions}
            return dict(action.choices), help_text
    return {}, {}


def run_cli_audit(path: Path = DEFAULT_PYPROJECT_PATH) -> CliAudit:
    # Imported lazily to avoid a module cycle while generator.cli registers this audit.
    from generator.cli import create_parser

    errors: list[str] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        console_script = (
            data.get("project", {}).get("scripts", {}).get("immersive-adventure-quests")
        )
    except (OSError, tomllib.TOMLDecodeError) as exc:
        console_script = None
        errors.append(f"cannot read packaging metadata: {exc}")

    parsers, help_text = _command_parsers(create_parser())
    commands = tuple(sorted(parsers))
    expected = set(EXPECTED_COMMANDS)
    actual = set(commands)
    missing = tuple(sorted(expected - actual))
    unexpected = tuple(sorted(actual - expected))
    without_help = tuple(
        sorted(name for name in parsers if not (help_text.get(name) or "").strip())
    )

    if console_script != EXPECTED_CONSOLE_SCRIPT:
        errors.append("immersive-adventure-quests must point to " f"{EXPECTED_CONSOLE_SCRIPT}")

    return CliAudit(
        commands=commands,
        missing_commands=missing,
        undocumented_commands=unexpected,
        commands_without_help=without_help,
        console_script=console_script,
        errors=tuple(errors),
    )
