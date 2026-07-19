from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from generator.github_release import create_github_release_plan, publish_github_release


@dataclass(frozen=True, slots=True)
class GitHubReleaseContract:
    deterministic_plan: bool
    assets_verified: bool
    dry_run_safe: bool
    explicit_publish_verified: bool
    unsafe_inputs_rejected: bool
    workflow_present: bool

    @property
    def is_clean(self) -> bool:
        return all((self.deterministic_plan, self.assets_verified, self.dry_run_safe,
                    self.explicit_publish_verified, self.unsafe_inputs_rejected, self.workflow_present))

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", **{
            field: getattr(self, field) for field in (
                "deterministic_plan", "assets_verified", "dry_run_safe",
                "explicit_publish_verified", "unsafe_inputs_rejected", "workflow_present")}}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return f"GitHub release publishing contract: {'PASS' if self.is_clean else 'FAIL'}"


def run_github_release_contract() -> GitHubReleaseContract:
    with tempfile.TemporaryDirectory(prefix="ftbq-github-release-") as temporary:
        root = Path(temporary)
        notes = root / "notes.md"
        notes.write_text("Release notes\n", encoding="utf-8")
        first = root / "app.zip"
        second = root / "update.json"
        first.write_bytes(b"archive")
        second.write_bytes(b"{}")
        plan = create_github_release_plan("owner/project", "v1.2.3", [second, first], notes_file=notes)
        repeated = create_github_release_plan("owner/project", "v1.2.3", [first, second], notes_file=notes)
        dry = publish_github_release(plan)
        calls: list[tuple[str, ...]] = []
        published = publish_github_release(plan, execute=True, runner=lambda command: (calls.append(tuple(command)) or 0))
        rejected = False
        try:
            create_github_release_plan("not-a-repo", "latest", [first], notes_file=notes)
        except ValueError:
            rejected = True
        return GitHubReleaseContract(
            deterministic_plan=plan.to_dict() == repeated.to_dict(),
            assets_verified=all(asset.size_bytes > 0 and len(asset.sha256) == 64 for asset in plan.assets),
            dry_run_safe=dry.is_clean and not dry.executed,
            explicit_publish_verified=published.is_clean and published.executed and bool(calls),
            unsafe_inputs_rejected=rejected,
            workflow_present=Path(".github/workflows/publish-release.yml").is_file(),
        )
