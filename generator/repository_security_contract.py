from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.repository_security import run_repository_security_policy, scan_repository_secrets


@dataclass(frozen=True, slots=True)
class RepositorySecurityContract:
    repository_clean: bool
    private_key_detected: bool
    github_token_detected: bool
    exclusions_supported: bool
    workflow_permissions_valid: bool
    ci_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, field) for field in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{field: getattr(self, field) for field in self.__dataclass_fields__}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Repository secret scanning and workflow permission contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_repository_security_contract() -> RepositorySecurityContract:
    repository = run_repository_security_policy(excluded_paths=("tests/fixtures",))
    with tempfile.TemporaryDirectory(prefix="ftbq-repository-security-") as temporary:
        root = Path(temporary)
        (root / "private.txt").write_text("-----BEGIN " + "PRIVATE KEY-----\n", encoding="utf-8")
        (root / "token.txt").write_text("ghp_" + "A" * 36 + "\n", encoding="utf-8")
        _, findings = scan_repository_secrets(root)
        _, excluded = scan_repository_secrets(root, excluded_paths=("private.txt", "token.txt"))
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    return RepositorySecurityContract(
        repository_clean=repository.is_clean,
        private_key_detected=any(item.kind == "private-key" for item in findings),
        github_token_detected=any(item.kind == "github-token" for item in findings),
        exclusions_supported=not excluded,
        workflow_permissions_valid=not repository.workflow_errors,
        ci_integrated="repository-security-audit --format json" in workflow,
    )
