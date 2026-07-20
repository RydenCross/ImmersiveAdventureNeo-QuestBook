from generator.desktop_launcher_contract import run_desktop_launcher_contract


def test_desktop_launcher_contract_passes() -> None:
    result = run_desktop_launcher_contract()
    assert result.is_clean, result.format()


def test_desktop_launcher_contract_json_status_matches() -> None:
    result = run_desktop_launcher_contract()
    assert '"status": "pass"' in result.format_json()


def test_archive_source_launch_plan_opens_editor_directly(tmp_path) -> None:
    from generator.desktop_launcher import build_editor_launch_plan

    source = tmp_path / "My Pack.mrpack"
    plan = build_editor_launch_plan(
        source=source,
        workspace_root=tmp_path / "workspace",
        python_executable="FTBQuestMaker.exe",
    )
    assert plan.command[:4] == (
        "FTBQuestMaker.exe",
        "-m",
        "generator",
        "quest-editor-serve",
    )
    assert str(source) in plan.command
    assert plan.source == str(source)
