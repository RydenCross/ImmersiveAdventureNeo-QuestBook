from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Iterable

from generator.output_writer import atomic_write_text

PREFERENCES_SCHEMA_VERSION = "1.0"
DEFAULT_APPLICATION_ROOT = Path.home() / ".ftb-quest-maker"
DEFAULT_PREFERENCES_PATH = DEFAULT_APPLICATION_ROOT / "preferences.json"
DEFAULT_MAX_INSTANCES = 500


def _normalized_path(value: str | Path) -> str:
    return Path(value).expanduser().absolute().as_posix()


def _normalized_roots(values: Iterable[str | Path]) -> tuple[str, ...]:
    unique: dict[str, str] = {}
    for value in values:
        normalized = _normalized_path(value)
        unique.setdefault(normalized.casefold(), normalized)
    return tuple(sorted(unique.values(), key=str.casefold))


@dataclass(frozen=True, slots=True)
class DesktopPreferences:
    schema_version: str = PREFERENCES_SCHEMA_VERSION
    first_run_complete: bool = False
    workspace_root: str = DEFAULT_APPLICATION_ROOT.as_posix()
    search_roots: tuple[str, ...] = ()
    open_browser: bool = True
    max_instances: int = DEFAULT_MAX_INSTANCES
    last_instance_id: str = ""

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.schema_version != PREFERENCES_SCHEMA_VERSION:
            errors.append(f"unsupported preferences schema: {self.schema_version}")
        if not self.workspace_root.strip():
            errors.append("workspace_root must not be empty")
        if not 1 <= self.max_instances <= 5000:
            errors.append("max_instances must be between 1 and 5000")
        normalized = _normalized_roots(self.search_roots)
        if normalized != self.search_roots:
            errors.append("search_roots must be normalized, unique, and sorted")
        return tuple(errors)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "first_run_complete": self.first_run_complete,
            "workspace_root": self.workspace_root,
            "search_roots": list(self.search_roots),
            "open_browser": self.open_browser,
            "max_instances": self.max_instances,
            "last_instance_id": self.last_instance_id,
        }

    @classmethod
    def from_dict(cls, payload: object) -> DesktopPreferences:
        if not isinstance(payload, dict):
            raise ValueError("preferences payload must be an object")
        roots = payload.get("search_roots", [])
        if not isinstance(roots, list) or not all(isinstance(item, str) for item in roots):
            raise ValueError("search_roots must be a list of paths")
        preferences = cls(
            schema_version=str(payload.get("schema_version", "")),
            first_run_complete=bool(payload.get("first_run_complete", False)),
            workspace_root=_normalized_path(
                str(payload.get("workspace_root", DEFAULT_APPLICATION_ROOT))
            ),
            search_roots=_normalized_roots(roots),
            open_browser=bool(payload.get("open_browser", True)),
            max_instances=int(payload.get("max_instances", DEFAULT_MAX_INSTANCES)),
            last_instance_id=str(payload.get("last_instance_id", "")),
        )
        errors = preferences.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return preferences

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class PreferencesLoadResult:
    preferences: DesktopPreferences
    source: str
    warnings: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.warnings

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "warning",
            "source": self.source,
            "warnings": list(self.warnings),
            "preferences": self.preferences.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class FirstRunSetupResult:
    preferences_path: str
    preferences: DesktopPreferences
    created_directories: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return self.preferences.first_run_complete and not self.preferences.validate()

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "preferences_path": self.preferences_path,
            "created_directories": list(self.created_directories),
            "preferences": self.preferences.to_dict(),
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Desktop first-run setup: {'PASS' if self.is_clean else 'FAIL'}",
            f"Preferences: {self.preferences_path}.",
            f"Workspace: {self.preferences.workspace_root}.",
            f"Search roots: {len(self.preferences.search_roots)}.",
            f"Open browser: {'yes' if self.preferences.open_browser else 'no'}.",
            f"Maximum instances: {self.preferences.max_instances}.",
        ))


def default_preferences(*, application_root: Path = DEFAULT_APPLICATION_ROOT) -> DesktopPreferences:
    return DesktopPreferences(workspace_root=_normalized_path(application_root))


def load_desktop_preferences(
    path: Path = DEFAULT_PREFERENCES_PATH,
    *,
    application_root: Path | None = None,
) -> PreferencesLoadResult:
    selected_path = Path(path).expanduser()
    fallback = default_preferences(application_root=application_root or selected_path.parent)
    if not selected_path.is_file():
        return PreferencesLoadResult(fallback, "default")
    try:
        payload = json.loads(selected_path.read_text(encoding="utf-8"))
        preferences = DesktopPreferences.from_dict(payload)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return PreferencesLoadResult(
            fallback,
            "recovered",
            (f"invalid preferences ignored: {exc}",),
        )
    return PreferencesLoadResult(preferences, "file")


def save_desktop_preferences(
    preferences: DesktopPreferences,
    path: Path = DEFAULT_PREFERENCES_PATH,
) -> Path:
    errors = preferences.validate()
    if errors:
        raise ValueError("; ".join(errors))
    selected_path = Path(path).expanduser()
    atomic_write_text(selected_path, preferences.format_json() + "\n")
    return selected_path


def complete_first_run_setup(
    *,
    preferences_path: Path = DEFAULT_PREFERENCES_PATH,
    workspace_root: Path = DEFAULT_APPLICATION_ROOT,
    search_roots: Iterable[Path] = (),
    open_browser: bool = True,
    max_instances: int = DEFAULT_MAX_INSTANCES,
) -> FirstRunSetupResult:
    normalized_workspace = Path(workspace_root).expanduser().absolute()
    preferences = DesktopPreferences(
        first_run_complete=True,
        workspace_root=normalized_workspace.as_posix(),
        search_roots=_normalized_roots(search_roots),
        open_browser=open_browser,
        max_instances=max_instances,
    )
    errors = preferences.validate()
    if errors:
        raise ValueError("; ".join(errors))
    created = []
    for directory in (
        normalized_workspace,
        normalized_workspace / "workspaces",
        normalized_workspace / "logs",
    ):
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory.as_posix())
    save_desktop_preferences(preferences, preferences_path)
    return FirstRunSetupResult(
        Path(preferences_path).expanduser().as_posix(),
        preferences,
        tuple(created),
    )


def update_last_instance(
    preferences: DesktopPreferences,
    instance_id: str,
    *,
    path: Path = DEFAULT_PREFERENCES_PATH,
) -> DesktopPreferences:
    updated = replace(preferences, last_instance_id=instance_id)
    save_desktop_preferences(updated, path)
    return updated
