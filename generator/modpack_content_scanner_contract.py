from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from generator.modpack_content_scanner import scan_modpack_content


def _synthetic_mod_jar(*, include_broken_json: bool = False) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "META-INF/neoforge.mods.toml",
            'modLoader="javafml"\nloaderVersion="[1,)"\nlicense="MIT"\n'
            '[[mods]]\nmodId="scanner_demo"\nversion="1.0.0"\n'
            'displayName="Scanner Demo"\n',
        )
        archive.writestr("scanner_demo/Exploit.class", b"not executable by the scanner")
        archive.writestr("assets/scanner_demo/items/copper_gear.json", "{}")
        archive.writestr("assets/scanner_demo/items/assembly_machine.json", "{}")
        archive.writestr(
            "assets/scanner_demo/lang/en_us.json",
            json.dumps({
                "item.scanner_demo.copper_gear": "Copper Gear",
                "item.scanner_demo.assembly_machine": "Assembly Machine",
            }),
        )
        archive.writestr(
            "data/scanner_demo/recipes/copper_gear.json",
            json.dumps({
                "type": "minecraft:crafting_shaped",
                "pattern": [" C ", "C C", " C "],
                "key": {"C": {"item": "minecraft:copper_ingot"}},
                "result": {"id": "scanner_demo:copper_gear", "count": 1},
            }),
        )
        archive.writestr(
            "data/scanner_demo/recipes/assembly_machine.json",
            json.dumps({
                "type": "minecraft:crafting_shaped",
                "pattern": ["GGG", "GIG", "GGG"],
                "key": {
                    "G": {"item": "scanner_demo:copper_gear"},
                    "I": {"tag": "c:ingots/iron"},
                },
                "result": {"id": "scanner_demo:assembly_machine", "count": 1},
            }),
        )
        archive.writestr(
            "data/scanner_demo/advancements/root.json",
            json.dumps({
                "display": {
                    "icon": {"id": "scanner_demo:copper_gear"},
                    "title": "Getting Geared",
                    "description": "Craft the first component.",
                },
                "criteria": {"has_gear": {"trigger": "minecraft:inventory_changed"}},
            }),
        )
        archive.writestr(
            "data/scanner_demo/advancements/assembly.json",
            json.dumps({
                "parent": "scanner_demo:root",
                "display": {
                    "icon": {"id": "scanner_demo:assembly_machine"},
                    "title": "Automated Assembly",
                    "description": "Build the assembly machine.",
                },
                "criteria": {"has_machine": {"trigger": "minecraft:inventory_changed"}},
            }),
        )
        archive.writestr(
            "data/scanner_demo/tags/items/machines.json",
            json.dumps({"replace": False, "values": ["scanner_demo:assembly_machine"]}),
        )
        if include_broken_json:
            archive.writestr("data/scanner_demo/recipes/broken.json", "{")
    return output.getvalue()


def _synthetic_pack(path: Path, *, include_broken_json: bool = False) -> None:
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "modrinth.index.json",
            json.dumps({
                "formatVersion": 1,
                "game": "minecraft",
                "name": "Scanner Contract Pack",
                "versionId": "1.0",
                "dependencies": {"minecraft": "1.21.1", "neoforge": "21.1.1"},
                "files": [],
            }),
        )
        archive.writestr(
            "overrides/mods/scanner-demo.jar",
            _synthetic_mod_jar(include_broken_json=include_broken_json),
        )


@dataclass(frozen=True, slots=True)
class ModpackContentScannerContract:
    recipes_detected: bool
    advancements_detected: bool
    registries_detected: bool
    tags_detected: bool
    dependency_chain_detected: bool
    candidate_budget_respected: bool
    corrupt_json_isolated: bool
    jar_code_not_executed: bool

    @property
    def is_clean(self) -> bool:
        return all((
            self.recipes_detected,
            self.advancements_detected,
            self.registries_detected,
            self.tags_detected,
            self.dependency_chain_detected,
            self.candidate_budget_respected,
            self.corrupt_json_isolated,
            self.jar_code_not_executed,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "recipes_detected": self.recipes_detected,
            "advancements_detected": self.advancements_detected,
            "registries_detected": self.registries_detected,
            "tags_detected": self.tags_detected,
            "dependency_chain_detected": self.dependency_chain_detected,
            "candidate_budget_respected": self.candidate_budget_respected,
            "corrupt_json_isolated": self.corrupt_json_isolated,
            "jar_code_not_executed": self.jar_code_not_executed,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Modpack content scanner contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Recipes detected: {'yes' if self.recipes_detected else 'no'}.",
            f"Advancements detected: {'yes' if self.advancements_detected else 'no'}.",
            f"Registry entries detected: {'yes' if self.registries_detected else 'no'}.",
            f"Tags detected: {'yes' if self.tags_detected else 'no'}.",
            f"Dependency chain detected: {'yes' if self.dependency_chain_detected else 'no'}.",
            f"Candidate budget respected: {'yes' if self.candidate_budget_respected else 'no'}.",
            f"Corrupt JSON isolated: {'yes' if self.corrupt_json_isolated else 'no'}.",
            f"JAR code not executed: {'yes' if self.jar_code_not_executed else 'no'}.",
        ))


def run_modpack_content_scanner_contract() -> ModpackContentScannerContract:
    with TemporaryDirectory(prefix="modpack-content-scanner-contract-") as temporary:
        root = Path(temporary)
        pack = root / "contract.mrpack"
        _synthetic_pack(pack)
        result = scan_modpack_content(pack, candidate_limit=20)

        candidates = {candidate.objective_id: candidate for candidate in result.candidates}
        gear = candidates.get("scanner_demo:copper_gear")
        machine = candidates.get("scanner_demo:assembly_machine")
        dependency_chain = bool(
            gear
            and machine
            and gear.candidate_id in machine.prerequisite_candidates
        )

        broken_pack = root / "broken-content.mrpack"
        _synthetic_pack(broken_pack, include_broken_json=True)
        broken = scan_modpack_content(broken_pack, candidate_limit=20)

        marker = root / "executed.txt"
        return ModpackContentScannerContract(
            recipes_detected=len(result.recipes) == 2,
            advancements_detected=len(result.advancements) == 2,
            registries_detected=len(result.registries) >= 2,
            tags_detected=len(result.tags) == 1,
            dependency_chain_detected=dependency_chain,
            candidate_budget_respected=len(result.candidates) <= result.candidate_limit == 20,
            corrupt_json_isolated=broken.is_clean and any("broken.json" in item for item in broken.warnings),
            jar_code_not_executed=not marker.exists(),
        )
