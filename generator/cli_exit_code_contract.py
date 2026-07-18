from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
import json

from generator.audit_registry_contract import AUDIT_REGISTRY


@dataclass(frozen=True, slots=True)
class CliExitCodeContract:
    commands_checked: int
    missing_handlers: tuple[str, ...]
    passing_exit_mismatches: tuple[str, ...]
    failing_exit_mismatches: tuple[str, ...]
    invalid_json: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_handlers, self.passing_exit_mismatches, self.failing_exit_mismatches, self.invalid_json))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "commands_checked": self.commands_checked,
            "missing_handlers": list(self.missing_handlers),
            "passing_exit_mismatches": list(self.passing_exit_mismatches),
            "failing_exit_mismatches": list(self.failing_exit_mismatches),
            "invalid_json": list(self.invalid_json),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"CLI exit-code contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Commands checked: {self.commands_checked}.",
            f"Missing handlers: {len(self.missing_handlers)}.",
            f"Passing exit mismatches: {len(self.passing_exit_mismatches)}.",
            f"Failing exit mismatches: {len(self.failing_exit_mismatches)}.",
            f"Invalid JSON: {len(self.invalid_json)}.",
        ]
        for label, values in (
            ("Missing handler", self.missing_handlers),
            ("Pass mismatch", self.passing_exit_mismatches),
            ("Fail mismatch", self.failing_exit_mismatches),
            ("Invalid JSON", self.invalid_json),
        ):
            lines.extend(f"{label}: {value}" for value in values)
        return "\n".join(lines)


class _SyntheticFailure:
    is_clean = False

    def format_json(self) -> str:
        return json.dumps({"status": "fail", "synthetic": True}, indent=2, sort_keys=True)

    def format(self) -> str:
        return "Synthetic failure"


def run_cli_exit_code_contract() -> CliExitCodeContract:
    # Lazy imports avoid cycles while CLI registration is assembled.
    import generator.cli as cli
    from generator.cli_audit import _command_parsers

    commands = tuple(item.command for item in AUDIT_REGISTRY if item.report and item.command != "cli-exit-code-audit")
    parsers, _ = _command_parsers(cli.create_parser())
    missing = tuple(sorted(command for command in commands if command not in parsers))

    pass_mismatches: list[str] = []
    fail_mismatches: list[str] = []
    invalid: list[str] = []
    representative = "packaging-audit"

    stdout = StringIO()
    with redirect_stdout(stdout):
        pass_code = cli.main([representative, "--format", "json"])
    try:
        payload = json.loads(stdout.getvalue())
        if payload.get("status") != "pass":
            pass_mismatches.append(representative)
    except (TypeError, ValueError, json.JSONDecodeError):
        invalid.append(representative)
    if pass_code != 0:
        pass_mismatches.append(representative)

    original = cli.run_packaging_audit
    cli.run_packaging_audit = lambda: _SyntheticFailure()
    try:
        stdout = StringIO()
        with redirect_stdout(stdout):
            fail_code = cli.main([representative, "--format", "json"])
        try:
            payload = json.loads(stdout.getvalue())
            if payload.get("status") != "fail":
                fail_mismatches.append(representative)
        except (TypeError, ValueError, json.JSONDecodeError):
            invalid.append(f"{representative}:fail")
        if fail_code == 0:
            fail_mismatches.append(representative)
    finally:
        cli.run_packaging_audit = original

    return CliExitCodeContract(
        commands_checked=len(commands),
        missing_handlers=missing,
        passing_exit_mismatches=tuple(sorted(set(pass_mismatches))),
        failing_exit_mismatches=tuple(sorted(set(fail_mismatches))),
        invalid_json=tuple(sorted(set(invalid))),
    )
