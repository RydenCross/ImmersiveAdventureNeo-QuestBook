# Report Refresh Contract

Commit 75 adds a single dependency-safe command for regenerating every checked-in audit report.

```bash
python -m generator report-refresh
python -m generator report-refresh --format json
```

The command uses the validated report refresh order, writes each JSON file atomically, rejects invalid renderer output, and leaves the two archive-derived reports until the end.

The companion contract is available through:

```bash
python -m generator report-refresh-audit
```
