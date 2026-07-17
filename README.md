# Immersive Adventure Neo Quest Builder

A deterministic Python authoring toolkit and generated FTB Quests v13 questbook for **Immersive Adventure Neo** on Minecraft 1.21.1/NeoForge.

## Current questbook

- 13 chapters
- 656 quests
- 223 optional quests
- Welcome, Survival, Mining, Exploration
- Create and Create Addons
- Actually Additions
- Ars Nouveau
- Apotheosis
- Applied Energistics 2
- Mekanism
- Endgame and Challenges

## Build

```bash
python -m generator
```

Generated files are written to:

```text
output/config/ftbquests/quests/
```

## Validate generated SNBT

```bash
python -m generator lint output/config/ftbquests/quests
```

## Audit authored content

```bash
python -m generator audit --strict
```

The audit summarizes chapter and quest totals, optional quests, task and reward coverage, empty descriptions, taskless quests, and duplicate titles.

## Verify item IDs against installed mods

```bash
python -m generator registry-audit /path/to/instance/mods --strict
```

The registry audit checks chapter icons, quest icons, item tasks, and item rewards against mod JAR assets or JSON registry exports. It supports text or JSON reports and can write directly to a file.

```bash
python -m generator registry-audit /path/to/instance/mods --format json --output reports/registry.json
python -m generator registry-manifest --output reports/quest-item-manifest.json
```

See [`docs/REGISTRY_AUDIT.md`](docs/REGISTRY_AUDIT.md) for supported formats and limitations.

## Run the complete release gate

```bash
python -m generator release-check
```

This builds the questbook in a temporary directory, reparses and validates the generated SNBT, runs the authored-content audit, and verifies registry-manifest totals. Use `--output <directory>` to keep the generated files. Use `--format json --report-output reports/release-check.json` to create a machine-readable release record.

## Test

```bash
pytest -q
```

The repository uses deterministic IDs, cross-chapter dependency checks, generated-file regression tests, and validator coverage to keep the questbook stable as content evolves.
