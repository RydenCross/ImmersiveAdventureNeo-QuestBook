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

## Compare release reports

```bash
python -m generator release-compare reports/baseline.json reports/current.json --strict
```

This detects new validation or content-quality defects, authored/generated mismatches, and unexpected decreases in questbook or registry-manifest totals. See [`docs/RELEASE_COMPARISON.md`](docs/RELEASE_COMPARISON.md).

## Test

```bash
pytest -q
```

The repository uses deterministic IDs, cross-chapter dependency checks, generated-file regression tests, and validator coverage to keep the questbook stable as content evolves.


## Quest dependency audit

Validate progression cycles, reachability, duplicate prerequisites, and chapter entry paths:

```bash
python -m generator dependency-audit --strict
```

Machine-readable reports are supported; see [`docs/DEPENDENCY_AUDIT.md`](docs/DEPENDENCY_AUDIT.md).

### Progression graph export

```bash
python -m generator dependency-graph --output reports/dependency-graph.dot
python -m generator dependency-graph --format json --output reports/dependency-graph.json
```

See [`docs/DEPENDENCY_GRAPH.md`](docs/DEPENDENCY_GRAPH.md).

## Progression metrics

Measure critical-path depth, high fan-out bottlenecks, and cross-chapter routes:

```bash
python -m generator progression-metrics
python -m generator progression-metrics --format json --output reports/progression-metrics.json
```

See [`docs/PROGRESSION_METRICS.md`](docs/PROGRESSION_METRICS.md).
