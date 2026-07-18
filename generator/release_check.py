from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from content import create_project
from generator.audit import audit_project
from generator.build import build
from generator.parser import FTBQuestParser
from generator.registry_audit import format_reference_manifest
from generator.validator import ProjectValidator


@dataclass(frozen=True, slots=True)
class ReleaseCheckReport:
    chapters: int
    quests: int
    optional_quests: int
    generated_chapters: int
    generated_quests: int
    validation_errors: int
    validation_warnings: int
    empty_descriptions: int
    taskless_quests: int
    duplicate_titles: int
    manifest_references: int
    manifest_unique_items: int
    manifest_namespaces: int

    @property
    def is_clean(self) -> bool:
        return not any(
            (
                self.validation_errors,
                self.validation_warnings,
                self.empty_descriptions,
                self.taskless_quests,
                self.duplicate_titles,
                self.chapters != self.generated_chapters,
                self.quests != self.generated_quests,
            )
        )

    def to_dict(self) -> dict[str, int | bool | str]:
        data: dict[str, int | bool | str] = asdict(self)
        data["status"] = "pass" if self.is_clean else "fail"
        data["is_clean"] = self.is_clean
        return data

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        status = "PASS" if self.is_clean else "FAIL"
        return "\n".join(
            (
                f"Release check: {status}",
                f"Authored content: {self.chapters} chapter(s), {self.quests} quest(s), "
                f"{self.optional_quests} optional.",
                f"Generated content: {self.generated_chapters} chapter(s), "
                f"{self.generated_quests} quest(s).",
                f"Validation: {self.validation_errors} error(s), "
                f"{self.validation_warnings} warning(s).",
                f"Content quality: {self.empty_descriptions} empty description(s), "
                f"{self.taskless_quests} taskless quest(s), "
                f"{self.duplicate_titles} duplicate title(s).",
                f"Registry manifest: {self.manifest_references} reference(s), "
                f"{self.manifest_unique_items} unique item id(s), "
                f"{self.manifest_namespaces} namespace(s).",
            )
        )


def run_release_check(output: Path | None = None) -> ReleaseCheckReport:
    project = create_project()
    audit = audit_project(project)
    authored_validation = ProjectValidator().validate(project)

    manifest = json.loads(format_reference_manifest(project))
    manifest_summary = manifest["summary"]

    if output is None:
        with TemporaryDirectory(prefix="ian-release-check-") as temporary:
            return _check_generated(
                project=project,
                audit=audit,
                authored_validation=authored_validation,
                manifest_summary=manifest_summary,
                destination=Path(temporary),
            )

    output.mkdir(parents=True, exist_ok=True)
    return _check_generated(
        project=project,
        audit=audit,
        authored_validation=authored_validation,
        manifest_summary=manifest_summary,
        destination=output,
    )


def _check_generated(
    *, project, audit, authored_validation, manifest_summary, destination: Path
) -> ReleaseCheckReport:
    quests_root = build(destination, quiet=True)
    generated = FTBQuestParser().load(quests_root)
    generated_validation = ProjectValidator().validate(generated)
    errors = len(authored_validation.errors) + len(generated_validation.errors)
    warnings = len(authored_validation.warnings) + len(generated_validation.warnings)

    return ReleaseCheckReport(
        chapters=len(project.chapters),
        quests=len(project.quests),
        optional_quests=audit.optional_quests,
        generated_chapters=len(generated.chapters),
        generated_quests=len(generated.quests),
        validation_errors=errors,
        validation_warnings=warnings,
        empty_descriptions=len(audit.empty_descriptions),
        taskless_quests=len(audit.taskless_quests),
        duplicate_titles=len(audit.duplicate_titles),
        manifest_references=manifest_summary["references"],
        manifest_unique_items=manifest_summary["unique_item_ids"],
        manifest_namespaces=manifest_summary["namespaces"],
    )
