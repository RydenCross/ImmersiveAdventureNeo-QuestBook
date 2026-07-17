# Progression guard

`python -m generator progression-guard` compares the current authored progression graph with the checked-in limits in `reports/progression-budget.json`.

The guard protects against accidental questbook shrinkage, dependency removal, critical-path growth, excessive bottlenecks, excessive direct fan-out, and unexpected cross-chapter coupling.

Generate a machine-readable report with:

```bash
python -m generator progression-guard --format json --output reports/progression-guard.json
```

Update the budget deliberately when an intentional progression redesign changes one of these limits. Budget changes should be reviewed together with the generated progression metrics.
