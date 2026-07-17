# Quality Gate

Run every repository-safe release safeguard with one command:

```bash
python -m generator quality-gate
```

For CI or tooling, write the combined result as JSON:

```bash
python -m generator quality-gate --format json --output reports/quality-gate.json
```

The gate runs the release, dependency, progression, identity, contract, reward, task,
chapter, text, determinism, output-manifest, and report-freshness checks. It exits with
status 1 when any check reports a defect and status 0 only when every check passes.

The combined report identifies each failed check while the individual checked-in reports
retain the detailed findings.
