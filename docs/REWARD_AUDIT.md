# Reward Integrity Audit

The reward integrity audit validates authored quest rewards without freezing reward
content behind a baseline. It is intended to catch malformed rewards before FTB
Quests files are generated.

Run the human-readable audit:

```bash
python -m generator reward-audit
```

Write a machine-readable CI report:

```bash
python -m generator reward-audit --format json --output reports/reward-audit.json
```

Use `--strict` to return a non-zero exit status when structural reward defects are
found.

The audit reports:

- globally duplicated reward IDs;
- malformed item identifiers;
- non-positive or non-integer item counts;
- non-item rewards with missing data;
- reward type totals; and
- terminal quests without rewards as informational review candidates.

Rewardless terminal quests do not fail the audit because some branches are designed
to end with narrative or progression-only completion.
