from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from content import create_project
from generator.cli import main
from generator.registry_audit import audit_registry, load_archive, load_json


def test_json_registry_supports_items_and_explicit_namespaces(tmp_path: Path) -> None:
    source = tmp_path / "registry.json"
    source.write_text(
        json.dumps({"namespaces": ["example"], "items": ["example:known", "other:item"]}),
        encoding="utf-8",
    )

    items, namespaces = load_json(source)

    assert items == {"example:known", "other:item"}
    assert namespaces == {"example", "other"}


def test_archive_registry_reads_modern_item_definitions_and_models(tmp_path: Path) -> None:
    source = tmp_path / "example.jar"
    with ZipFile(source, "w") as archive:
        archive.writestr("assets/example/items/modern_item.json", "{}")
        archive.writestr("assets/example/models/item/legacy_item.json", "{}")
        archive.writestr("assets/example/models/block/not_an_item.json", "{}")

    items, namespaces = load_archive(source)

    assert items == {"example:modern_item", "example:legacy_item"}
    assert namespaces == {"example"}


def test_registry_audit_only_flags_covered_namespaces(tmp_path: Path) -> None:
    source = tmp_path / "registry.json"
    source.write_text(json.dumps({"namespaces": ["minecraft"], "items": []}), encoding="utf-8")

    audit = audit_registry(create_project(), [source])

    assert audit.missing
    assert all(reference.item_id.startswith("minecraft:") for reference in audit.missing)
    assert all(not reference.item_id.startswith("minecraft:") for reference in audit.unverifiable)


def test_registry_audit_cli_strict_fails_for_missing_items(tmp_path: Path, capsys) -> None:
    source = tmp_path / "registry.json"
    source.write_text(json.dumps({"namespaces": ["minecraft"], "items": []}), encoding="utf-8")

    assert main(["registry-audit", str(source), "--strict"]) == 1
    assert "MISSING" in capsys.readouterr().out


def test_registry_audit_json_report_is_machine_readable(tmp_path: Path, capsys) -> None:
    source = tmp_path / "registry.json"
    source.write_text(json.dumps({"namespaces": ["minecraft"], "items": []}), encoding="utf-8")

    assert main(["registry-audit", str(source), "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["summary"]["missing"] > 0
    assert report["summary"]["clean"] is False
    assert report["namespaces"] == ["minecraft"]


def test_registry_audit_can_write_report_file(tmp_path: Path, capsys) -> None:
    source = tmp_path / "registry.json"
    output = tmp_path / "reports" / "registry.json"
    source.write_text(json.dumps({"items": ["minecraft:stone"]}), encoding="utf-8")

    assert main(["registry-audit", str(source), "--format", "json", "--output", str(output)]) == 0

    assert capsys.readouterr().out == ""
    assert json.loads(output.read_text(encoding="utf-8"))["summary"]["references"] > 0


def test_registry_manifest_groups_references_by_namespace(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"

    assert main(["registry-manifest", "--output", str(output)]) == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))

    assert manifest["summary"]["references"] > 0
    assert "minecraft" in manifest["namespaces"]
    assert "quest_icon" in manifest["namespaces"]["minecraft"]
