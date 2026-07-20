# Release Manifest Contract

The release manifest contract builds the deterministic release ZIP and records every packaged file with its path, uncompressed byte size, and SHA-256 digest.

Run the audit:

```bash
python -m generator release-manifest-audit
```

Generate the checked-in JSON report:

```bash
python -m generator release-manifest-audit --format json --output reports/release-manifest-audit.json
```

The contract fails when the generated manifest and independently read ZIP disagree about entry names, sizes, or content digests. The manifest status report is excluded from the release payload to avoid self-referential checksums.
