from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from generator.release_reproducibility_audit import _build_archive

DEFAULT_MAX_ARCHIVE_BYTES = 2_000_000
DEFAULT_MIN_SAVINGS_RATIO = 0.05
DEFAULT_MAX_ENTRY_BYTES = 1_000_000


@dataclass(frozen=True, slots=True)
class ReleaseArchiveCompressionContract:
    archive_entries: int
    archive_bytes: int
    uncompressed_bytes: int
    compressed_bytes: int
    savings_ratio: float
    stored_entries: tuple[str, ...]
    oversized_entries: tuple[str, ...]
    archive_budget_exceeded: bool
    savings_budget_missed: bool

    @property
    def is_clean(self) -> bool:
        return not any((
            self.stored_entries,
            self.oversized_entries,
            self.archive_budget_exceeded,
            self.savings_budget_missed,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "archive_bytes": self.archive_bytes,
            "uncompressed_bytes": self.uncompressed_bytes,
            "compressed_bytes": self.compressed_bytes,
            "savings_ratio": round(self.savings_ratio, 6),
            "stored_entries": list(self.stored_entries),
            "oversized_entries": list(self.oversized_entries),
            "archive_budget_exceeded": self.archive_budget_exceeded,
            "savings_budget_missed": self.savings_budget_missed,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release archive compression contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Archive bytes: {self.archive_bytes}.",
            f"Uncompressed bytes: {self.uncompressed_bytes}.",
            f"Compressed bytes: {self.compressed_bytes}.",
            f"Savings ratio: {self.savings_ratio:.2%}.",
            f"Stored entries: {len(self.stored_entries)}.",
            f"Oversized entries: {len(self.oversized_entries)}.",
            f"Archive budget exceeded: {'yes' if self.archive_budget_exceeded else 'no'}.",
            f"Savings budget missed: {'yes' if self.savings_budget_missed else 'no'}.",
        ))


def verify_release_archive_compression(
    archive_path: Path,
    *,
    max_archive_bytes: int = DEFAULT_MAX_ARCHIVE_BYTES,
    min_savings_ratio: float = DEFAULT_MIN_SAVINGS_RATIO,
    max_entry_bytes: int = DEFAULT_MAX_ENTRY_BYTES,
) -> ReleaseArchiveCompressionContract:
    if max_archive_bytes < 1 or max_entry_bytes < 1:
        raise ValueError("byte budgets must be positive")
    if not 0 <= min_savings_ratio < 1:
        raise ValueError("min_savings_ratio must be between 0 and 1")
    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
    uncompressed = sum(info.file_size for info in infos)
    compressed = sum(info.compress_size for info in infos)
    savings = 0.0 if uncompressed == 0 else 1.0 - (compressed / uncompressed)
    return ReleaseArchiveCompressionContract(
        archive_entries=len(infos),
        archive_bytes=archive_path.stat().st_size,
        uncompressed_bytes=uncompressed,
        compressed_bytes=compressed,
        savings_ratio=savings,
        stored_entries=tuple(info.filename for info in infos if info.compress_type != ZIP_DEFLATED),
        oversized_entries=tuple(info.filename for info in infos if info.file_size > max_entry_bytes),
        archive_budget_exceeded=archive_path.stat().st_size > max_archive_bytes,
        savings_budget_missed=bool(infos) and savings < min_savings_ratio,
    )


def run_release_archive_compression_contract(
    root: Path = Path('.'),
) -> ReleaseArchiveCompressionContract:
    root = root.resolve()
    with TemporaryDirectory() as directory:
        archive_path = Path(directory) / "release.zip"
        _build_archive(root, archive_path)
        return verify_release_archive_compression(archive_path)
