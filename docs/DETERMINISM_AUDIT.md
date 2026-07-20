# Build Determinism Audit

The build determinism audit runs the quest generator twice in isolated temporary directories and compares every generated file byte-for-byte.

```bash
python -m generator determinism-audit --strict
```

Write a machine-readable report with:

```bash
python -m generator determinism-audit --strict --format json --output reports/determinism-audit.json
```

The audit fails when a generated file disappears, an unexpected file appears, or any file differs between the two builds. The report also records a SHA-256 digest of the complete generated tree so release artifacts can be compared precisely.
