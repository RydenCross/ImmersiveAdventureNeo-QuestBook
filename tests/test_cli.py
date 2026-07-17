from generator.cli import main


def test_lint_command_accepts_valid_fixture(capsys) -> None:
    result = main(["lint", "tests/fixtures/ftbquests/quests"])
    output = capsys.readouterr().out
    assert result == 0
    assert "0 error(s)" in output


def test_release_check_command_passes(capsys) -> None:
    result = main(["release-check"])
    output = capsys.readouterr().out

    assert result == 0
    assert "Release check: PASS" in output
    assert "656 quest(s)" in output
