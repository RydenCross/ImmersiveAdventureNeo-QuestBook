from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ReleaseInstallValidation:
    windows_artifact: str | None
    linux_artifact: str | None
    verified_files: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "windows_artifact": self.windows_artifact,
            "linux_artifact": self.linux_artifact,
            "verified_files": list(self.verified_files),
            "errors": list(self.errors),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksums(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not _SHA256.fullmatch(parts[0]):
            raise ValueError(f"invalid checksum line {number}")
        name = parts[1].lstrip(" *").strip()
        if not name or Path(name).name != name or name in result:
            raise ValueError(f"invalid or duplicate checksum filename on line {number}")
        result[name] = parts[0]
    return result


def validate_release_installers(
    assets: Path,
    checksums: Path,
    update_metadata: Path,
    *,
    minimum_bytes: int = 4096,
) -> ReleaseInstallValidation:
    assets = assets.resolve()
    errors: list[str] = []
    verified: list[str] = []
    windows = sorted(assets.rglob("*.exe"))
    linux = sorted(assets.rglob("*.AppImage"))
    if len(windows) != 1:
        errors.append(f"expected exactly one Windows installer, found {len(windows)}")
    if len(linux) != 1:
        errors.append(f"expected exactly one Linux AppImage, found {len(linux)}")

    try:
        manifest = _read_checksums(checksums)
    except (OSError, UnicodeError, ValueError) as exc:
        manifest = {}
        errors.append(f"invalid checksum manifest: {exc}")

    selected = windows[:1] + linux[:1]
    for path in selected:
        try:
            size = path.stat().st_size
            header = path.read_bytes()[:4]
        except OSError as exc:
            errors.append(f"cannot read {path.name}: {exc}")
            continue
        if size < minimum_bytes:
            errors.append(f"artifact is unexpectedly small: {path.name} ({size} bytes)")
        if path.suffix.casefold() == ".exe" and not header.startswith(b"MZ"):
            errors.append(f"Windows installer lacks PE MZ signature: {path.name}")
        if path.suffix == ".AppImage":
            if header != b"\x7fELF":
                errors.append(f"AppImage lacks ELF signature: {path.name}")
            if os.name != "nt" and not os.access(path, os.X_OK):
                errors.append(f"AppImage is not executable: {path.name}")
        digest = _sha256(path)
        expected = manifest.get(path.name)
        if expected is None:
            errors.append(f"checksum manifest is missing {path.name}")
        elif expected != digest:
            errors.append(f"checksum mismatch for {path.name}")
        else:
            verified.append(path.name)

    try:
        payload = json.loads(update_metadata.read_text(encoding="utf-8"))
        text = json.dumps(payload, sort_keys=True)
        for path in selected:
            digest = _sha256(path)
            if path.name not in text:
                errors.append(f"update metadata does not reference {path.name}")
            if digest not in text:
                errors.append(f"update metadata does not bind SHA-256 for {path.name}")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid update metadata: {exc}")

    return ReleaseInstallValidation(
        windows[0].name if len(windows) == 1 else None,
        linux[0].name if len(linux) == 1 else None,
        tuple(sorted(verified)),
        tuple(sorted(set(errors))),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate release installers before publication.")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--update", type=Path, required=True)
    parser.add_argument("--minimum-bytes", type=int, default=4096)
    args = parser.parse_args(argv)
    result = validate_release_installers(
        args.assets, args.checksums, args.update, minimum_bytes=args.minimum_bytes
    )
    print(result.format_json())
    return 0 if result.is_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
