# Release Reproducibility Audit

Run:

```bash
python -m generator release-reproducibility-audit
```

Write JSON output:

```bash
python -m generator release-reproducibility-audit --format json --output reports/release-reproducibility-audit.json
```

The audit creates two independent release archives and compares their entry names and SHA-256 content digests. It fails when an entry is missing, unexpectedly added, or differs byte-for-byte between builds. Raw ZIP digests are reported for diagnostics, while the normalized content-tree digest is the reproducibility contract.
