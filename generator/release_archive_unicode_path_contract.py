from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unicodedata
from zipfile import ZipFile

from generator.release_reproducibility_audit import _build_archive


@dataclass(frozen=True, slots=True)
class ReleaseArchiveUnicodePathContract:
    archive_entries: int
    non_nfc_paths: tuple[str, ...]
    compatibility_collisions: tuple[str, ...]
    control_character_paths: tuple[str, ...]
    bidi_control_paths: tuple[str, ...]
    non_portable_segments: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.non_nfc_paths, self.compatibility_collisions,
                        self.control_character_paths, self.bidi_control_paths,
                        self.non_portable_segments))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "archive_entries": self.archive_entries,
            "non_nfc_paths": list(self.non_nfc_paths),
            "compatibility_collisions": list(self.compatibility_collisions),
            "control_character_paths": list(self.control_character_paths),
            "bidi_control_paths": list(self.bidi_control_paths),
            "non_portable_segments": list(self.non_portable_segments),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Release archive Unicode path contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Archive entries: {self.archive_entries}.",
            f"Non-NFC paths: {len(self.non_nfc_paths)}.",
            f"Compatibility collisions: {len(self.compatibility_collisions)}.",
            f"Control-character paths: {len(self.control_character_paths)}.",
            f"Bidirectional-control paths: {len(self.bidi_control_paths)}.",
            f"Non-portable path segments: {len(self.non_portable_segments)}.",
        ))


def _collisions(groups: dict[str, list[str]]) -> tuple[str, ...]:
    return tuple(sorted(
        f"{key}: {', '.join(sorted(values))}"
        for key, values in groups.items() if len(set(values)) > 1
    ))


def verify_release_archive_unicode_paths(archive_path: Path) -> ReleaseArchiveUnicodePathContract:
    non_nfc: list[str] = []
    compatibility: dict[str, list[str]] = {}
    controls: list[str] = []
    bidi: list[str] = []
    non_portable: list[str] = []
    bidi_classes = {"RLE", "LRE", "RLO", "LRO", "PDF", "RLI", "LRI", "FSI", "PDI"}

    with ZipFile(archive_path) as archive:
        infos = archive.infolist()
        for info in infos:
            name = info.filename
            if unicodedata.normalize("NFC", name) != name:
                non_nfc.append(name)
            key = unicodedata.normalize("NFKC", name).casefold()
            compatibility.setdefault(key, []).append(name)
            if any(unicodedata.category(ch) == "Cc" for ch in name):
                controls.append(name)
            if any(unicodedata.bidirectional(ch) in bidi_classes for ch in name):
                bidi.append(name)
            for segment in name.split("/"):
                if segment and (segment[-1:] in {" ", "."} or segment in {".", ".."}):
                    non_portable.append(name)
                    break

    return ReleaseArchiveUnicodePathContract(
        archive_entries=len(infos),
        non_nfc_paths=tuple(sorted(set(non_nfc))),
        compatibility_collisions=_collisions(compatibility),
        control_character_paths=tuple(sorted(set(controls))),
        bidi_control_paths=tuple(sorted(set(bidi))),
        non_portable_segments=tuple(sorted(set(non_portable))),
    )


def run_release_archive_unicode_path_contract() -> ReleaseArchiveUnicodePathContract:
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "release.zip"
        _build_archive(Path.cwd(), archive_path)
        return verify_release_archive_unicode_paths(archive_path)
