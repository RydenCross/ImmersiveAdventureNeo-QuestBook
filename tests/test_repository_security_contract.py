from pathlib import Path

from generator.repository_security import run_repository_security_policy, scan_repository_secrets
from generator.repository_security_contract import run_repository_security_contract


def test_repository_security_contract_passes() -> None:
    assert run_repository_security_contract().is_clean


def test_secret_scanner_detects_supported_secret_shapes(tmp_path: Path) -> None:
    (tmp_path / "secret.txt").write_text("github_pat_" + "A" * 50, encoding="utf-8")
    scanned, findings = scan_repository_secrets(tmp_path)
    assert scanned == 1
    assert findings[0].kind == "github-fine-grained-token"


def test_secret_scanner_honors_explicit_exclusions(tmp_path: Path) -> None:
    (tmp_path / "ignored.txt").write_text("ghp_" + "A" * 36, encoding="utf-8")
    _, findings = scan_repository_secrets(tmp_path, excluded_paths=("ignored.txt",))
    assert findings == ()


def test_repository_security_policy_serializes_status() -> None:
    payload = run_repository_security_policy(excluded_paths=("tests/fixtures",)).to_dict()
    assert payload["status"] == "pass"
