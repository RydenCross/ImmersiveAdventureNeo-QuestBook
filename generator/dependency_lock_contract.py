from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.dependency_lock import (
    lock_digest,
    parse_hashed_lock,
    reproducible_install_plan,
    write_lock_manifest,
)


@dataclass(frozen=True, slots=True)
class DependencyLockContract:
    repository_lock_valid: bool
    deterministic_digest: bool
    exact_pins_required: bool
    hashes_required: bool
    duplicate_names_rejected: bool
    reproducible_plan_hardened: bool
    atomic_manifest_write: bool
    ci_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, field) for field in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            **{field: getattr(self, field) for field in self.__dataclass_fields__},
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Locked dependency and hash verification contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_dependency_lock_contract() -> DependencyLockContract:
    repository_lock = Path("requirements-ci.lock")
    parsed = parse_hashed_lock(repository_lock)
    with tempfile.TemporaryDirectory(prefix="ftbq-dependency-lock-") as temporary:
        root = Path(temporary)
        valid = root / "valid.lock"
        valid.write_text(
            "alpha==1.2.3 --hash=sha256:" + "a" * 64 + "\n",
            encoding="utf-8",
        )
        exact_pins_required = False
        missing_hash_rejected = False
        duplicate_names_rejected = False
        try:
            invalid = root / "invalid.lock"
            invalid.write_text("alpha>=1\n", encoding="utf-8")
            parse_hashed_lock(invalid)
        except ValueError:
            exact_pins_required = True
        try:
            invalid = root / "missing-hash.lock"
            invalid.write_text("alpha==1\n", encoding="utf-8")
            parse_hashed_lock(invalid)
        except ValueError:
            missing_hash_rejected = True
        duplicate = root / "duplicate.lock"
        duplicate.write_text(
            "alpha==1 --hash=sha256:" + "a" * 64 + "\n"
            "Alpha==2 --hash=sha256:" + "b" * 64 + "\n",
            encoding="utf-8",
        )
        duplicate_names_rejected = not parse_hashed_lock(duplicate).is_clean
        output = write_lock_manifest(valid, root / "nested" / "manifest.json")
        plan = reproducible_install_plan(valid)
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        return DependencyLockContract(
            repository_lock_valid=parsed.is_clean,
            deterministic_digest=lock_digest(repository_lock) == lock_digest(repository_lock),
            exact_pins_required=exact_pins_required,
            hashes_required=missing_hash_rejected,
            duplicate_names_rejected=duplicate_names_rejected,
            reproducible_plan_hardened=(
                "--require-hashes" in plan
                and "--no-deps" in plan
                and "--only-binary=:all:" in plan
            ),
            atomic_manifest_write=output.is_file() and not output.with_name(output.name + ".tmp").exists(),
            ci_integrated="dependency-lock-audit" in workflow,
        )
