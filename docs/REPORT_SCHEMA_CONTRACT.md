# Report Schema Contract

The report schema contract keeps every registered audit report safe for CI and downstream automation.

```bash
python -m generator report-schema-audit
python -m generator report-schema-audit --format json --output reports/report-schema-audit.json
```

For every report registered in the central audit registry, the contract requires:

- the report file exists;
- the file is valid UTF-8 JSON;
- the top-level value is a JSON object;
- a top-level `status` field exists;
- `status` is either `pass` or `fail`.

The contract is part of the unified quality gate and report freshness guard.
