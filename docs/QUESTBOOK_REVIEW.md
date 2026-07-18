# Generated Questbook Review

The generated questbook review is the editorial and structural approval stage between blueprint generation and publishing an FTB Quests tree.

## Run the review

```bash
python -m generator questbook-review /path/to/modpack.mrpack
```

Generate a machine-readable report for an editor or application UI:

```bash
python -m generator questbook-review /path/to/modpack.mrpack \
  --target-quests 600 \
  --chapter-size 40 \
  --format json \
  --output questbook-review.json
```

Thresholds can be adjusted without changing the generated blueprint:

```bash
python -m generator questbook-review /path/to/modpack.mrpack \
  --low-confidence-threshold 0.80 \
  --min-description-words 10 \
  --max-chapter-quests 45 \
  --bottleneck-dependents 10
```

## Review coverage

The report checks:

- blueprint and FTB export validation errors;
- dangling prerequisites and dependency cycles;
- unsupported or malformed objective IDs;
- duplicate objectives;
- low-confidence and planner-marked quests;
- short or weak descriptions;
- missing reward decisions;
- oversized chapters;
- high-fan-out progression bottlenecks;
- quest-target shortfalls;
- root, leaf, edge, and maximum-depth progression metrics.

A `pass` status means no blocking structural errors were found. `publish_ready` remains false while warnings or editorial review items still need a human decision. Missing rewards are intentionally treated as review work rather than automatically invented rewards.

## Validate the reviewer

```bash
python -m generator questbook-review-audit
python -m generator questbook-review-audit \
  --format json \
  --output reports/questbook-review-audit.json
```

The contract verifies deterministic output, export validation, weak-description and reward detection, oversized chapters, bottlenecks, dangling dependencies, and invalid threshold handling.

## Review generated reward decisions

```bash
python -m generator questbook-review /path/to/modpack.mrpack \
  --reward-policy conservative
```

This applies the selected reward policy before review, allowing the report to distinguish complete reward decisions from unassigned quests.
