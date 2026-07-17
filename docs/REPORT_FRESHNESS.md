# Report Freshness Guard

The report freshness guard prevents checked-in machine-readable audit reports from drifting behind the authored questbook.

Run the guard with:

```bash
python -m generator report-freshness-guard
```

Write a machine-readable result with:

```bash
python -m generator report-freshness-guard \
  --format json \
  --output reports/report-freshness-guard.json
```

The guard regenerates each derived audit report in memory and compares its parsed JSON payload with the checked-in report. Whitespace and key ordering do not matter. Missing files, invalid JSON, or changed values fail the guard.

Protected derived reports include release, dependency, progression, identity, contract, task, reward, chapter, text, determinism, and generated-output manifest checks. Baselines and budgets are intentionally excluded because they are reviewed policy inputs rather than regenerated evidence.
