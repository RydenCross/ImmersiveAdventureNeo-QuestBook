# Release Archive Compression Contract

The release archive compression contract verifies that deterministic release ZIPs remain efficiently compressed and within explicit size budgets.

Run it with:

```bash
python -m generator release-archive-compression-audit
python -m generator release-archive-compression-audit --format json --output reports/release-archive-compression-audit.json
```

The audit rejects non-DEFLATE entries, oversized individual files, archives above the configured byte budget, and packages that fail the minimum compression-savings ratio.
