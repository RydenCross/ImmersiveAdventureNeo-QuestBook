# Progression Metrics

Use the progression metrics report to review questbook pacing and structural concentration after the dependency audit has passed.

```bash
python -m generator progression-metrics
```

The report measures:

- longest prerequisite-chain depth;
- quests at the deepest progression tier;
- bottleneck quests with four or more direct dependants;
- cross-chapter transition routes and their edge counts.

Write a machine-readable report for CI artifacts or visualization tools:

```bash
python -m generator progression-metrics \
  --format json \
  --output reports/progression-metrics.json
```

The analyzer intentionally rejects cyclic graphs because critical-path depth is undefined until dependency cycles are repaired with `dependency-audit`.
