# Quest Description and Instruction Generator

The description generator replaces short scanner-derived copy with deterministic player-facing instructions while staying grounded in data discovered from the modpack.

```bash
python -m generator quest-description-plan /path/to/modpack.mrpack \
  --target-quests 600 \
  --style guided \
  --format json \
  --output quest-description-plan.json
```

Available styles are `concise`, `guided`, and `detailed`.

The generator explains how each item or advancement objective completes, names prerequisite quests, lists known recipe inputs and accepted tags, and identifies the next generated milestones. Registry-only objectives receive explicit review guidance because the scanner did not confirm a recipe or advancement for them.

The text does not claim a specific machine, processing method, or original mod recipe unless that fact was discovered from pack data. It reminds players that pack scripts and recipe changes remain authoritative.

Validate the generator with:

```bash
python -m generator quest-description-audit
python -m generator quest-description-audit --format json --output reports/quest-description-audit.json
```

Export and review commands apply guided descriptions by default. Use `--description-style concise` or `--description-style detailed` to select another style.
