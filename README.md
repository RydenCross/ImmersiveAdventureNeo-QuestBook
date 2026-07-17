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

Protect progression complexity with checked-in limits:

```bash
python -m generator progression-guard
python -m generator progression-guard --format json --output reports/progression-guard.json
```

See [`docs/PROGRESSION_METRICS.md`](docs/PROGRESSION_METRICS.md).

## Release baseline guard

Protect release quality and content totals against the checked-in baseline:

```bash
python -m generator release-guard
```

After an intentional reviewed change, safely refresh the baseline:

```bash
python -m generator release-baseline reports/release-baseline.json
```

See `docs/RELEASE_GUARD.md` for details.

## Quest identity guard

Protect stable chapter and quest identities against accidental removals, renames, UUID changes, or chapter moves:

```bash
python -m generator identity-guard
python -m generator identity-guard --format json --output reports/identity-guard.json
```

After an intentional reviewed identity change, refresh the protected manifest:

```bash
python -m generator identity-baseline reports/quest-identity-baseline.json
```

See [`docs/IDENTITY_GUARD.md`](docs/IDENTITY_GUARD.md).

## Quest contract guard

Protect gameplay-facing quest contracts from accidental edits while allowing description and localization improvements:

```bash
python -m generator contract-guard
python -m generator contract-guard --format json --output reports/contract-guard.json
```

Refresh the baseline only after an intentional reviewed contract change:

```bash
python -m generator contract-baseline reports/quest-contract-baseline.json
```


## Reward integrity audit

Validate reward IDs and definitions before release:

```bash
python -m generator reward-audit --strict
python -m generator reward-audit --format json --output reports/reward-audit.json
```

See [`docs/REWARD_AUDIT.md`](docs/REWARD_AUDIT.md) for the validation rules.

## Task integrity audit

Validate completion-task IDs, required task data, and task coverage before release:

```bash
python -m generator task-audit --strict
python -m generator task-audit --strict --format json --output reports/task-audit.json
```

See [`docs/TASK_AUDIT.md`](docs/TASK_AUDIT.md) for the validation rules.

## Chapter integrity audit

Validate chapter identities, metadata, ordering, and quest coverage before release:

```bash
python -m generator chapter-audit --strict
python -m generator chapter-audit --strict --format json --output reports/chapter-audit.json
```

See [`docs/CHAPTER_AUDIT.md`](docs/CHAPTER_AUDIT.md) for the validation rules.



## Quest text quality audit

Run `python -m generator text-audit --strict` to detect placeholder copy, malformed formatting, duplicated substantive descriptions, and short descriptions that deserve review. See `docs/TEXT_AUDIT.md`.


## Build determinism audit

Verify that two isolated builds produce exactly the same files and bytes:

```bash
python -m generator determinism-audit --strict
python -m generator determinism-audit --strict --format json --output reports/determinism-audit.json
```

See [`docs/DETERMINISM_AUDIT.md`](docs/DETERMINISM_AUDIT.md).


## Generated output manifest guard

Protect the exact generated FTB Quests file set and contents:

```bash
python -m generator output-manifest-guard
python -m generator output-manifest-guard --format json --output reports/output-manifest-guard.json
```

Refresh the checked-in manifest after an intentional deterministic output change:

```bash
python -m generator output-manifest reports/generated-output-manifest.json
```

See [`docs/OUTPUT_MANIFEST.md`](docs/OUTPUT_MANIFEST.md).

### Report freshness guard

Verify that checked-in audit evidence still matches the current questbook:

```bash
python -m generator report-freshness-guard --format json \
  --output reports/report-freshness-guard.json
```

See [docs/REPORT_FRESHNESS.md](docs/REPORT_FRESHNESS.md).


## Unified quality gate

Run every repository-safe release safeguard in one CI-friendly command:

```bash
python -m generator quality-gate
python -m generator quality-gate --format json --output reports/quality-gate.json
```

See [`docs/QUALITY_GATE.md`](docs/QUALITY_GATE.md).


## Packaging audit

Run `python -m generator packaging-audit` to verify package discovery and the installed console command.

### CLI contract audit

Use the CLI contract audit to ensure every supported subcommand remains registered, documented with help text, and available through the installed console entry point:

```bash
python -m generator cli-audit
python -m generator cli-audit --format json --output reports/cli-audit.json
```


## Documentation contract audit

```bash
python -m generator documentation-audit
python -m generator documentation-audit --format json --output reports/documentation-audit.json
```

See [`docs/DOCUMENTATION_AUDIT.md`](docs/DOCUMENTATION_AUDIT.md).


## Repository hygiene audit

Detect caches, build artifacts, secret-like files, and oversized accidental additions:

```bash
python -m generator repository-hygiene-audit
python -m generator repository-hygiene-audit --format json --output reports/repository-hygiene-audit.json
python -m generator release-artifact-audit
python -m generator release-artifact-audit --format json --output reports/release-artifact-audit.json
```

See [`docs/REPOSITORY_HYGIENE.md`](docs/REPOSITORY_HYGIENE.md).


## Release reproducibility audit

```bash
python -m generator release-reproducibility-audit
```

Compares two independently created release archives by normalized entry names and SHA-256 content digests.
