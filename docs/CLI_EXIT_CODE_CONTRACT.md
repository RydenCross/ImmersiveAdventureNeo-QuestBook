# CLI Exit-Code Contract

The CLI exit-code contract verifies that audit commands use process status consistently with their JSON report status.

```bash
python -m generator cli-exit-code-audit
python -m generator cli-exit-code-audit --format json --output reports/cli-exit-code-audit.json
```

A passing report must return exit code `0`. A failing report must return a non-zero exit code. The audit performs both a real passing invocation and a synthetic failing invocation through the public CLI.
