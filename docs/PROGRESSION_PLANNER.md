# Progression Planner and Quest Blueprint Generator

The progression planner converts a scanned modpack into a reviewable, dependency-safe questbook blueprint. It does not write FTB Quests SNBT yet; the blueprint is the stable intermediate representation used by the next export stage.

## Generate a blueprint

```bash
python -m generator quest-blueprint /path/to/modpack.mrpack
```

Write machine-readable JSON:

```bash
python -m generator quest-blueprint /path/to/modpack.mrpack \
  --target-quests 600 \
  --chapter-size 40 \
  --format json \
  --output quest-blueprint.json
```

When `--target-quests` is omitted, the planner uses the target calculated by the modpack profile. Targets must be between 1 and 5000 quests. Chapter sizes must be between 5 and 100 quests.

## Planning behavior

The planner:

- uses the recipe, advancement, registry, and tag candidates from `modpack-content-scan`;
- selects candidates with deterministic round-robin mod coverage;
- includes prerequisite closure before selecting a dependent quest;
- keeps the selected graph acyclic and free of dangling quest prerequisites;
- groups quests by owning mod and gameplay category;
- splits large mod chapters at the configured chapter-size boundary;
- creates deterministic chapter order and quest coordinates;
- records cross-chapter prerequisites;
- marks low-confidence registry-only quests for manual review;
- reports a shortfall instead of inventing objectives that are not supported by pack metadata.

For a large pack with enough discovered content, the profile target can naturally reach roughly 500–600 quests. Packs with limited machine-readable content will produce fewer candidates and a visible shortfall warning.

## Blueprint structure

Each blueprint contains:

- pack and loader metadata;
- requested, available, and selected quest totals;
- ordered chapter definitions;
- stable quest and candidate IDs;
- item or advancement objectives;
- quest, item, and tag prerequisites;
- source provenance and confidence scores;
- deterministic layout coordinates;
- review-required flags and warnings.

## Validate the planner

```bash
python -m generator progression-planner-audit
python -m generator progression-planner-audit \
  --format json \
  --output reports/progression-planner-audit.json
```

The contract verifies target enforcement, dependency preservation, absence of dangling prerequisites, deterministic output, valid layout positions, review flags, and invalid-limit rejection.
