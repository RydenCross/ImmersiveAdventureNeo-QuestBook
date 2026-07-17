# Release Artifact Audit

The release artifact audit creates a temporary ZIP from the repository release tree and validates its contents before distribution.

```bash
python -m generator release-artifact-audit
python -m generator release-artifact-audit --format json --output reports/release-artifact-audit.json
```

It checks archive integrity, duplicate entries, invalid JSON, empty files, forbidden generated artifacts, and generated-output manifest coverage.
