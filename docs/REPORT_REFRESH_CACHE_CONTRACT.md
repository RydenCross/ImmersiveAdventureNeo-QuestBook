# Incremental Report Refresh Cache

Commit 88 adds an opt-in content-addressed cache to the checked-in report refresh workflow.

```bash
python -m generator report-refresh --incremental
python -m generator report-refresh --incremental --format json
```

The cache is stored at `reports/.report-refresh-cache.json` by default. It records each report's input fingerprint and output SHA-256. A renderer is skipped only when both values still match, so deleted, modified, or corrupted report files are rebuilt safely.

Input fingerprints combine conservative source scopes with declared audit-report dependencies. Generator changes invalidate all reports, while documentation-only, test-only, and content-only changes can avoid unrelated renderers. Report dependency digests preserve the validated regeneration order and convergence behavior.

Use a custom cache location when needed:

```bash
python -m generator report-refresh --incremental --cache path/to/cache.json
```

Validate the cache behavior with:

```bash
python -m generator report-refresh-cache-audit
python -m generator report-refresh-cache-audit --format json --output reports/report-refresh-cache-audit.json
```

The contract proves cold-cache population, full cache hits, selective invalidation, tampered-output rebuilding, corrupt-cache recovery, and default fingerprint coverage.
