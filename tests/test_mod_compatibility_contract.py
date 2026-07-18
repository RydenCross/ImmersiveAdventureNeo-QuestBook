from __future__ import annotations

import json
from pathlib import Path

from generator.mod_compatibility_contract import run_mod_compatibility_contract


def test_checked_in_mod_compatibility_policy_is_clean() -> None:
    result = run_mod_compatibility_contract()
    assert result.is_clean
    assert result.minecraft_versions == ("1.21.1",)
    assert result.loader == "NeoForge"
    assert result.declared_mods == 6
    assert result.missing_content_modules == ()


def test_contract_detects_missing_module_and_invalid_status(tmp_path: Path) -> None:
    content = tmp_path / "content"
    (content / "known").mkdir(parents=True)
    (content / "known" / "chapter.py").write_text("x = 1\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({
        "platform": {"minecraft": ["1.21.1"], "loader": "NeoForge", "loader_version": "21.1.x", "quest_format": "FTB Quests v13"},
        "mods": [{"content_module": "other", "mod_id": "other", "display_name": "Other", "requirement": "required", "version_policy": "pack-managed", "status": "broken"}],
        "incompatibilities": [],
    }), encoding="utf-8")
    result = run_mod_compatibility_contract(policy, content)
    assert not result.is_clean
    assert result.missing_content_modules == ("known",)
    assert result.unknown_content_modules == ("other",)
    assert "mods[0].status" in result.invalid_entries
