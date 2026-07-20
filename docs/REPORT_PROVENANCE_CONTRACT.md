# Report Provenance Contract

The report provenance contract ensures every tracked audit report can be traced to the registered CLI command that generates it.

```bash
python -m generator report-provenance-audit
python -m generator report-provenance-audit --format json --output reports/report-provenance-audit.json
```

The audit verifies that each report registration has an existing CLI command and freshness renderer, and that no unregistered report renderer is present. Its JSON output includes the complete report-to-command provenance map.
