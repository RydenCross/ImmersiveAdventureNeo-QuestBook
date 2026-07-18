from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.audit_registry_contract import AUDIT_REGISTRY


@dataclass(frozen=True, slots=True)
class CliOutputContract:
    commands_checked: int
    renderers_checked: int
    missing_json_format: tuple[str, ...]
    missing_output_option: tuple[str, ...]
    invalid_json: tuple[str, ...]
    output_mismatches: tuple[str, ...]
    nonzero_exit_codes: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.missing_json_format,
                self.missing_output_option,
                self.invalid_json,
                self.output_mismatches,
                self.nonzero_exit_codes,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "commands_checked": self.commands_checked,
            "renderers_checked": self.renderers_checked,
            "missing_json_format": list(self.missing_json_format),
            "missing_output_option": list(self.missing_output_option),
            "invalid_json": list(self.invalid_json),
            "output_mismatches": list(self.output_mismatches),
            "nonzero_exit_codes": list(self.nonzero_exit_codes),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"CLI output contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Commands checked: {self.commands_checked}.",
            f"Renderers checked: {self.renderers_checked}.",
            f"Missing JSON format: {len(self.missing_json_format)}.",
            f"Missing output option: {len(self.missing_output_option)}.",
            f"Invalid JSON: {len(self.invalid_json)}.",
            f"Output mismatches: {len(self.output_mismatches)}.",
            f"Nonzero exit codes: {len(self.nonzero_exit_codes)}.",
        ]
        for label, values in (
            ("Missing JSON", self.missing_json_format),
            ("Missing output", self.missing_output_option),
            ("Invalid JSON", self.invalid_json),
            ("Mismatch", self.output_mismatches),
            ("Nonzero exit", self.nonzero_exit_codes),
        ):
            lines.extend(f"{label}: {value}" for value in values)
        return "\n".join(lines)


def run_cli_output_contract() -> CliOutputContract:
    # Lazy imports avoid cycles while CLI and freshness registration are assembled.
    from generator.cli import create_parser, main
    from generator.cli_audit import _command_parsers

    commands = tuple(
        item.command
        for item in AUDIT_REGISTRY
        if item.report and item.command != "cli-output-audit"
    )
    parsers, _ = _command_parsers(create_parser())
    missing_json: list[str] = []
    missing_output: list[str] = []

    for command in commands:
        parser = parsers.get(command)
        if parser is None:
            missing_json.append(command)
            missing_output.append(command)
            continue
        actions = {action.dest: action for action in parser._actions}
        format_action = actions.get("format")
        choices = set(getattr(format_action, "choices", ()) or ())
        if "json" not in choices:
            missing_json.append(command)
        if "output" not in actions:
            missing_output.append(command)

    invalid: list[str] = []
    for item in AUDIT_REGISTRY:
        if not item.report or item.command == "cli-output-audit":
            continue
        path = Path("reports") / item.report
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            invalid.append(item.command)

    # Exercise stdout/file parity through the public CLI on a lightweight command.
    mismatches: list[str] = []
    nonzero: list[str] = []
    representative = "packaging-audit"
    stdout = StringIO()
    with redirect_stdout(stdout):
        stdout_code = main([representative, "--format", "json"])
    with TemporaryDirectory(prefix="cli-output-contract-") as temporary:
        output = Path(temporary) / "report.json"
        with redirect_stdout(StringIO()):
            file_code = main(
                [representative, "--format", "json", "--output", str(output)]
            )
        if stdout_code != 0 or file_code != 0:
            nonzero.append(representative)
        try:
            stdout_payload = json.loads(stdout.getvalue())
            file_payload = json.loads(output.read_text(encoding="utf-8"))
            if stdout_payload != file_payload:
                mismatches.append(representative)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            invalid.append(representative)

    return CliOutputContract(
        commands_checked=len(commands),
        renderers_checked=len(commands),
        missing_json_format=tuple(sorted(set(missing_json))),
        missing_output_option=tuple(sorted(set(missing_output))),
        invalid_json=tuple(sorted(set(invalid))),
        output_mismatches=tuple(sorted(set(mismatches))),
        nonzero_exit_codes=tuple(sorted(set(nonzero))),
    )
