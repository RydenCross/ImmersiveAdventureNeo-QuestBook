from pathlib import Path
import subprocess

import pytest

from generator.desktop_setup import (
    DesktopPreferences,
    complete_first_run_setup,
    load_desktop_preferences,
    save_desktop_preferences,
)
from generator.native_distribution import (
    build_native_distribution,
    create_native_distribution_plan,
    detect_native_platform,
)


def test_first_run_setup_persists_normalized_preferences(tmp_path: Path) -> None:
    preferences_path = tmp_path / "preferences.json"
    workspace = tmp_path / "workspace"
    root_b = tmp_path / "b"
    root_a = tmp_path / "a"
    result = complete_first_run_setup(
        preferences_path=preferences_path,
        workspace_root=workspace,
        search_roots=(root_b, root_a, root_b),
        open_browser=False,
        max_instances=250,
    )
    loaded = load_desktop_preferences(preferences_path)
    assert result.is_clean
    assert loaded.is_clean
    assert loaded.preferences.first_run_complete
    assert loaded.preferences.search_roots == (
        root_a.absolute().as_posix(),
        root_b.absolute().as_posix(),
    )
    assert (workspace / "workspaces").is_dir()


def test_invalid_preferences_are_recovered_without_overwriting(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    path.write_text('{"schema_version": "99"}', encoding="utf-8")
    result = load_desktop_preferences(path)
    assert result.source == "recovered"
    assert result.warnings
    assert path.read_text(encoding="utf-8") == '{"schema_version": "99"}'


def test_preference_validation_rejects_invalid_instance_limit(tmp_path: Path) -> None:
    preferences = DesktopPreferences(
        first_run_complete=True,
        workspace_root=tmp_path.as_posix(),
        max_instances=0,
    )
    with pytest.raises(ValueError, match="max_instances"):
        save_desktop_preferences(preferences, tmp_path / "preferences.json")


def test_native_build_plan_is_target_specific_and_deterministic(tmp_path: Path) -> None:
    first = create_native_distribution_plan(
        "windows", destination=tmp_path, python_executable="python-test"
    )
    second = create_native_distribution_plan(
        "windows", destination=tmp_path, python_executable="python-test"
    )
    linux = create_native_distribution_plan(
        "linux", destination=tmp_path, python_executable="python-test"
    )
    assert first == second
    assert first.executable_name.endswith(".exe")
    assert not linux.executable_name.endswith(".exe")
    assert "PyInstaller" in first.command


def test_native_build_dry_run_does_not_execute_runner(tmp_path: Path) -> None:
    calls = []

    def runner(*args: object, **kwargs: object) -> subprocess.CompletedProcess[object]:
        calls.append((args, kwargs))
        return subprocess.CompletedProcess([], 0)

    result = build_native_distribution(
        "linux",
        destination=tmp_path,
        dry_run=True,
        system_name="Linux",
        runner=runner,
    )
    assert result.is_clean
    assert result.dry_run
    assert calls == []


def test_native_build_rejects_cross_platform_execution(tmp_path: Path) -> None:
    result = build_native_distribution(
        "windows",
        destination=tmp_path,
        system_name="Linux",
        pyinstaller_available=True,
    )
    assert not result.is_clean
    assert result.return_code == 2


def test_native_platform_detection_rejects_unsupported_platform() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        detect_native_platform("Darwin")
