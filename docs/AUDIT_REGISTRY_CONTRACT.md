# Audit Registry Contract

Run the registry audit with:

```bash
python -m generator audit-registry-audit
```

Write a machine-readable report with:

```bash
python -m generator audit-registry-audit --format json --output reports/audit-registry-audit.json
```

The contract prevents release safeguards from being only partially integrated. Every registered audit must have a unique quality-gate name and CLI command, and every report-producing audit must be present in the report freshness inventory.
