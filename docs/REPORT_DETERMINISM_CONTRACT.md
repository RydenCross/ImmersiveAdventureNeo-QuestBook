# Report Determinism Contract

The report determinism contract verifies that every registered audit renderer produces the same JSON payload when run twice against an unchanged repository state.

Run it with:

```bash
python -m generator report-determinism-audit
```

Write the machine-readable result with:

```bash
python -m generator report-determinism-audit --format json --output reports/report-determinism-audit.json
```

The contract reports nondeterministic renderers and renderers that fail to return valid JSON. The contract excludes its own renderer from the recursive comparison; its serializer is covered by direct regression tests.
