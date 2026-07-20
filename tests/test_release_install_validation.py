from __future__ import annotations

import hashlib
import json
from pathlib import Path

from generator.release_install_validation import validate_release_installers


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    assets = tmp_path / "assets"
    assets.mkdir()
    exe = assets / "FTBQuestMaker-1.2.3-Setup.exe"
    app = assets / "FTBQuestMaker-1.2.3-x86_64.AppImage"
    exe.write_bytes(b"MZ" + b"x" * 5000)
    app.write_bytes(b"\x7fELF" + b"y" * 5000)
    app.chmod(0o755)
    checksums = assets / "SHA256SUMS"
    checksums.write_text(
        f"{_digest(exe)}  {exe.name}\n{_digest(app)}  {app.name}\n",
        encoding="utf-8",
    )
    update = assets / "update.json"
    update.write_text(json.dumps({
        "windows": {"filename": exe.name, "sha256": _digest(exe)},
        "linux": {"filename": app.name, "sha256": _digest(app)},
    }), encoding="utf-8")
    return assets, checksums, update


def test_valid_release_installers_pass(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    result = validate_release_installers(assets, checksums, update)
    assert result.is_clean
    assert len(result.verified_files) == 2


def test_rejects_bad_signature_and_checksum(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    exe = next(assets.glob("*.exe"))
    exe.write_bytes(b"NO" + b"z" * 5000)
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("MZ signature" in error for error in result.errors)
    assert any("checksum mismatch" in error for error in result.errors)


def test_rejects_missing_platform_artifact(tmp_path: Path) -> None:
    assets, checksums, update = _fixture(tmp_path)
    next(assets.glob("*.AppImage")).unlink()
    result = validate_release_installers(assets, checksums, update)
    assert not result.is_clean
    assert any("exactly one Linux" in error for error in result.errors)
