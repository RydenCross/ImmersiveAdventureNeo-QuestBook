# Release Report Comparison

Use `release-compare` to compare two JSON reports produced by `release-check`.

```bash
python -m generator release-check --format json --report-output reports/current.json
python -m generator release-compare reports/baseline.json reports/current.json --strict
```

The comparison reports every changed metric and treats the following as regressions:

- New validation errors or warnings
- New empty descriptions, taskless quests, or duplicate titles
- Decreased chapter, quest, optional-quest, generated-content, or registry-manifest totals
- Authored and generated chapter or quest totals no longer matching
- A current release report marked as failed

Use JSON output for CI or other automation:

```bash
python -m generator release-compare \
  reports/baseline.json reports/current.json \
  --strict --format json --output reports/release-comparison.json
```

Intentional reductions can be reviewed from the report and accepted by replacing the baseline report after the change is approved.
