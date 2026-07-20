# Report Refresh Idempotence Contract

Run the contract with:

```bash
python -m generator report-refresh-idempotence-audit
```

Generate the tracked JSON report with:

```bash
python -m generator report-refresh-idempotence-audit --format json --output reports/report-refresh-idempotence-audit.json
```

The contract runs the same deterministic report renderers twice. The first refresh must converge, and the second refresh must complete in one pass without changing file contents or modification times. This protects the report workflow from unnecessary rewrites after a stable fixed point has already been reached.
