# Report Consistency Contract

The report consistency contract verifies that checked-in audit reports are internally coherent.

```bash
python -m generator report-consistency-audit
```

Use `--format json` and `--output reports/report-consistency-audit.json` for machine-readable output.

The contract rejects passing reports that still contain defect lists, failing reports with no recorded defects, and summary counts that disagree with their corresponding detail lists.
