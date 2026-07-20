from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from generator.output_writer import atomic_write_text

DEFAULT_CLI_PATH = Path("generator/cli.py")


@dataclass(frozen=True, slots=True)
class ReportWriteSafetyContract:
    direct_cli_writes: tuple[str, ...]
    successful_replacement: bool
    failed_write_preserved_destination: bool
    temporary_files_left_behind: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return (
            not self.direct_cli_writes
            and self.successful_replacement
            and self.failed_write_preserved_destination
            and not self.temporary_files_left_behind
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "direct_cli_writes": list(self.direct_cli_writes),
            "successful_replacement": self.successful_replacement,
            "failed_write_preserved_destination": self.failed_write_preserved_destination,
            "temporary_files_left_behind": list(self.temporary_files_left_behind),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Report write-safety contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Direct CLI writes: {len(self.direct_cli_writes)}.",
                f"Successful atomic replacement: {self.successful_replacement}.",
                "Failed write preserved destination: "
                f"{self.failed_write_preserved_destination}.",
                f"Temporary files left behind: {len(self.temporary_files_left_behind)}.",
            )
        )


def run_report_write_safety_contract(
    cli_path: Path = DEFAULT_CLI_PATH,
) -> ReportWriteSafetyContract:
    source = cli_path.read_text(encoding="utf-8")
    direct_writes = tuple(
        sorted(
            line.strip()
            for line in source.splitlines()
            if ".write_text(" in line and "atomic_write_text" not in line
        )
    )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        destination = root / "report.json"
        destination.write_text('{"old": true}\n', encoding="utf-8")
        atomic_write_text(destination, '{"new": true}\n')
        successful = destination.read_text(encoding="utf-8") == '{"new": true}\n'

        destination.write_text('{"stable": true}\n', encoding="utf-8")
        try:
            with patch("generator.output_writer.os.replace", side_effect=OSError("blocked")):
                atomic_write_text(destination, '{"partial": true}\n')
        except OSError:
            pass
        preserved = destination.read_text(encoding="utf-8") == '{"stable": true}\n'
        leftovers = tuple(sorted(path.name for path in root.iterdir() if path != destination))

    return ReportWriteSafetyContract(
        direct_cli_writes=direct_writes,
        successful_replacement=successful,
        failed_write_preserved_destination=preserved,
        temporary_files_left_behind=leftovers,
    )
