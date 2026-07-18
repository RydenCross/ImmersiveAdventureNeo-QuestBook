# Report Refresh Convergence Contract

The report refresh command must leave the tracked report set at a stable fixed point in one invocation.

## Run the audit

```bash
python -m generator report-refresh-convergence-audit
```

Use `--format json` for machine-readable output or `--output` to write a report.

## Guarantees

The contract verifies that refresh passes continue until no report payload changes, unstable renderers fail after the configured pass limit, and invalid pass limits are rejected. The default `report-refresh` command allows four passes and reports the number required to converge.
