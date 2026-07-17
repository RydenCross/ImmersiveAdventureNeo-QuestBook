from pathlib import Path

from generator.output_manifest import (
    OutputFile,
    OutputManifest,
    build_output_manifest,
    compare_output_manifests,
    create_output_manifest,
    load_output_manifest,
    refresh_output_manifest,
)


def manifest(*files: OutputFile) -> OutputManifest:
    return OutputManifest(len(files), sum(file.size for file in files), "tree", tuple(files))


def test_create_output_manifest_hashes_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("alpha", encoding="utf-8")
    result = create_output_manifest(tmp_path)
    assert result.file_count == 1
    assert result.total_bytes == 5
    assert result.files[0].path == "a.txt"
    assert len(result.files[0].sha256) == 64


def test_compare_output_manifests_detects_all_change_types() -> None:
    baseline = manifest(OutputFile("gone", 1, "a"), OutputFile("changed", 1, "a"))
    current = manifest(OutputFile("new", 1, "b"), OutputFile("changed", 2, "b"))
    result = compare_output_manifests(baseline, current)
    assert result.missing_files == ("gone",)
    assert result.unexpected_files == ("new",)
    assert result.changed_files == ("changed",)
    assert not result.is_clean


def test_compare_output_manifests_accepts_identical_files() -> None:
    value = manifest(OutputFile("same", 3, "abc"))
    assert compare_output_manifests(value, value).is_clean


def test_refresh_and_load_output_manifest(tmp_path: Path) -> None:
    destination = tmp_path / "manifest.json"
    refreshed = refresh_output_manifest(destination)
    loaded = load_output_manifest(destination)
    assert loaded == refreshed
    assert loaded.file_count > 0


def test_project_build_matches_checked_in_manifest() -> None:
    baseline = load_output_manifest(Path("reports/generated-output-manifest.json"))
    current = build_output_manifest()
    assert compare_output_manifests(baseline, current).is_clean
