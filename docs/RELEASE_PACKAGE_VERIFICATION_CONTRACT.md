# Release Package Verification Contract

The release package verification contract independently builds the repository release ZIP and cross-checks it against the release artifact and reproducibility audits.

It validates the archive entry count, byte-level archive checksum, content tree checksum, reproducibility result, and cache/package-metadata exclusions.

```bash
python -m generator release-package-verification-audit
python -m generator release-package-verification-audit --format json --output reports/release-package-verification-audit.json
```
