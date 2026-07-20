# CLI Output Contract

The CLI output contract verifies that every registered audit command supports a stable machine-readable interface.

```bash
python -m generator cli-output-audit
python -m generator cli-output-audit --format json --output reports/cli-output-audit.json
```

For each report-producing command, the contract checks that JSON written to standard output is valid, the command exits successfully, `--output` creates a file, and the file payload is identical to the standard-output payload.
