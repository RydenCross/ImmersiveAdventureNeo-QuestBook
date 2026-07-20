# Report Refresh Order Contract

The report refresh order contract protects dependency-safe regeneration of checked-in audit reports.

Run it with:

```bash
python -m generator report-refresh-order-audit
```

Generate JSON output with:

```bash
python -m generator report-refresh-order-audit --format json --output reports/report-refresh-order-audit.json
```

The contract requires every registered report to appear exactly once in the refresh order and requires archive-derived reports to be rendered last. Archive reports describe the final repository tree, so rendering them before other reports are updated would immediately make them stale.
