# Report Write-Safety Contract

The report write-safety contract protects checked-in and user-requested audit outputs from partial writes.

Run it with:

```bash
python -m generator report-write-safety-audit
python -m generator report-write-safety-audit --format json --output reports/report-write-safety-audit.json
```

The contract verifies that CLI report output uses the shared atomic writer, successful writes replace the destination, failed replacements preserve the previous file, and temporary files are cleaned up.
