from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.dependency_license import evaluate_dependency_licenses, write_license_inventory


@dataclass(frozen=True, slots=True)
class DependencyLicenseContract:
    repository_policy_clean: bool
    complete_inventory: bool
    denied_license_rejected: bool
    reviewed_exception_supported: bool
    invalid_exception_rejected: bool
    deterministic_output: bool
    atomic_write: bool
    ci_integrated: bool

    @property
    def is_clean(self) -> bool:
        return all(getattr(self, field) for field in self.__dataclass_fields__)

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{field: getattr(self, field) for field in self.__dataclass_fields__}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"Dependency license inventory and distribution policy contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_dependency_license_contract() -> DependencyLicenseContract:
    result = evaluate_dependency_licenses(Path("requirements-ci.lock"), Path("dependency-licenses.json"))
    with tempfile.TemporaryDirectory(prefix="ftbq-license-") as temporary:
        root = Path(temporary)
        lock = root / "lock.txt"
        lock.write_text("alpha==1.0 --hash=sha256:" + "a" * 64 + "\n", encoding="utf-8")
        denied_policy = root / "denied.json"
        denied_policy.write_text(json.dumps({"policy":{"allowed_spdx":["MIT"],"denied_spdx":["GPL-3.0-only"]},"packages":{"alpha":"GPL-3.0-only"},"reviewed_exceptions":{}}), encoding="utf-8")
        denied = evaluate_dependency_licenses(lock, denied_policy)
        excepted_policy = root / "excepted.json"
        excepted_policy.write_text(json.dumps({"policy":{"allowed_spdx":["MIT"],"denied_spdx":["GPL-3.0-only"]},"packages":{"alpha":"GPL-3.0-only"},"reviewed_exceptions":{"alpha":"Reviewed for tooling."}}), encoding="utf-8")
        excepted = evaluate_dependency_licenses(lock, excepted_policy)
        invalid_policy = root / "invalid.json"
        invalid_policy.write_text(json.dumps({"policy":{"allowed_spdx":["MIT"],"denied_spdx":[]},"packages":{"alpha":"MIT"},"reviewed_exceptions":{"ghost":"No package."}}), encoding="utf-8")
        invalid = evaluate_dependency_licenses(lock, invalid_policy)
        output = write_license_inventory(Path("requirements-ci.lock"), Path("dependency-licenses.json"), root / "nested" / "licenses.json")
        workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        return DependencyLicenseContract(
            repository_policy_clean=result.is_clean,
            complete_inventory=len(result.dependencies) == len(parse_count(Path("requirements-ci.lock"))),
            denied_license_rejected=not denied.is_clean and bool(denied.denied_packages),
            reviewed_exception_supported=excepted.is_clean,
            invalid_exception_rejected=not invalid.is_clean and bool(invalid.invalid_exceptions),
            deterministic_output=result.format_json() == evaluate_dependency_licenses(Path("requirements-ci.lock"), Path("dependency-licenses.json")).format_json(),
            atomic_write=output.is_file() and not output.with_name(output.name + ".tmp").exists(),
            ci_integrated="dependency-license-audit" in workflow,
        )


def parse_count(path: Path) -> tuple[str, ...]:
    return tuple(line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#"))
