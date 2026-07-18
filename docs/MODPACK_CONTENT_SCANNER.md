# Recipe, Advancement, and Registry Scanner

The content scanner is the second reusable engine component for the planned FTB Quest Maker app. It turns a modpack archive or instance into a normalized content inventory and a deterministic pool of progression-ready quest candidates.

## Scan a pack

```bash
python -m generator modpack-content-scan /path/to/modpack.mrpack
python -m generator modpack-content-scan /path/to/instance \
  --format json \
  --output content-profile.json
```

Use `--candidate-limit` to cap the generated candidate pool:

```bash
python -m generator modpack-content-scan pack.zip \
  --candidate-limit 600 \
  --format json \
  --output quest-candidates.json
```

When no explicit limit is supplied, the scanner uses the maximum quest recommendation from the pack profile produced by `modpack-scan`.

## Inputs

The scanner accepts the same inputs as the pack-profile scanner:

- Modrinth `.mrpack` files
- CurseForge export ZIPs
- Prism or normal Minecraft instance directories
- Server-pack ZIPs
- Plain `mods` directories
- Individual mod JARs

It inspects embedded mod JARs and bundled datapack resources without importing classes, executing scripts, or launching Minecraft.

## Detected resources

The scanner recognizes both traditional plural and modern singular datapack directory names where applicable.

### Recipes

Recipe JSON is normalized into:

- Recipe identifier and type
- Result item
- Direct ingredient item IDs
- Ingredient tag IDs
- Source archive and resource path

The result supports vanilla crafting recipes and many modded machine-recipe shapes because ingredient and result fields are inspected recursively.

### Advancements

Advancement JSON contributes:

- Advancement identifier
- Parent advancement
- Display title and description
- Icon item
- Criteria count
- Rewarded recipe IDs

Advancement parents become candidate prerequisites when both advancements are available.

### Registries and tags

Item registry entries are inferred from:

- `assets/<namespace>/items/*.json`
- `assets/<namespace>/models/item/*.json`

Datapack item, block, and fluid tags are normalized with their values and source paths. English language files are read when available so generated candidate titles can use player-facing item names.

## Quest candidates

The output combines three candidate sources:

1. Advancements, with the highest confidence and priority
2. Recipe outputs, with ingredient-derived dependencies
3. Registry-only items as lower-confidence fallback milestones

Each candidate records:

- Stable candidate ID
- Owning mod namespace
- Draft title and description
- FTB-compatible objective type and identifier
- Source kind and source identifier
- Candidate prerequisites
- Raw item and tag prerequisites
- Confidence and selection score

Candidates are selected deterministically with round-robin mod coverage so one content-heavy mod cannot consume the entire target. Dependency edges are filtered to keep the generated candidate graph acyclic.

## Current limitations

The scanner reads static resources only. It does not yet fully interpret:

- Runtime recipe registration
- KubeJS JavaScript logic beyond emitted datapack JSON
- CraftTweaker scripts
- Config-disabled recipes and items
- Machine-specific semantics such as power tiers or multiblock requirements
- Boss, dimension, fluid, entity, or biome progression

Those inputs will be layered onto the candidate graph in later phases. The current output is intended as a strong machine-generated draft that can be ranked, templated, and reviewed before FTB Quests export.

## Scanner contract

```bash
python -m generator modpack-content-scanner-audit
python -m generator modpack-content-scanner-audit \
  --format json \
  --output reports/modpack-content-scanner-audit.json
```

The deterministic contract verifies:

- Recipe extraction
- Advancement extraction
- Registry and tag discovery
- Recipe-output dependency chains
- Candidate-budget enforcement
- Isolation of malformed content JSON
- Non-execution of embedded JAR classes
