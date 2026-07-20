# Audit Performance Contract

The audit performance contract verifies that the registered safeguard inventory can be instrumented exactly once per audit and that the instrumentation layer respects a configurable runtime budget.

```bash
python -m generator audit-performance-audit
python -m generator audit-performance-audit --format json --output reports/audit-performance-audit.json
```

The default contract uses lightweight instrumentation probes rather than rerunning the complete quality gate recursively. Direct tests cover budget failures and machine-readable timing output. The five slowest probes are included for diagnostics.
