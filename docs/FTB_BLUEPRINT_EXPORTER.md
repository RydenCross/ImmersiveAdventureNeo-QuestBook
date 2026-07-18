# FTB Quests Blueprint Exporter

The exporter converts a generated quest blueprint into an installable FTB Quests v13 directory tree. It uses stable UUIDv5-derived FTB IDs, preserves quest prerequisites, emits item and advancement tasks, writes localized chapter and quest text, and validates the generated SNBT through a parser round trip.

## Export a modpack

```bash
python -m generator ftb-quest-export /path/to/modpack.mrpack \
  --destination generated/ftbquests \
  --target-quests 600 \
  --chapter-size 40
```

The destination becomes a standard `config/ftbquests`-style directory containing:

```text
quests/data.snbt
quests/chapter_groups.snbt
quests/chapters/*.snbt
quests/lang/en_us.snbt
quests/rewards.snbt
quests/loot_crates.snbt
```

Use `--format json --output export-summary.json` for a machine-readable summary.

## Safety and determinism

The exporter writes through a staging directory, removes stale chapter files from previous exports, validates all quest dependencies, rejects unsupported objective types, reparses the emitted SNBT, and reports a deterministic content-tree SHA-256.

Generated quests intentionally contain no automatic rewards. Review objectives, descriptions, progression, and rewards before publishing a questbook.

## Contract audit

```bash
python -m generator ftb-blueprint-exporter-audit
```

The audit verifies item and advancement task emission, dependency preservation, parser round trips, deterministic output, stale-file removal, and rejection of invalid blueprints.

## Optional generated rewards

Apply a generated reward policy during export:

```bash
python -m generator ftb-quest-export /path/to/modpack.mrpack \
  --destination generated/ftbquests \
  --reward-policy conservative
```

Supported policies are `none`, `conservative`, `balanced`, and `generous`. The default is `unassigned`.
