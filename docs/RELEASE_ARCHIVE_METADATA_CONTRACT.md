# Release Archive Metadata Contract

The release archive metadata contract verifies that deterministic packaging covers ZIP metadata as well as file contents.

```bash
python -m generator release-archive-metadata-audit
```

Generate the checked-in JSON report:

```bash
python -m generator release-archive-metadata-audit --format json --output reports/release-archive-metadata-audit.json
```

The contract requires lexicographically ordered, unique, path-safe entries; the canonical DOS epoch timestamp; regular-file `0644` permissions; DEFLATE compression; and no encrypted entries. This prevents source checkout timestamps, host permissions, or unsafe paths from changing the release artifact.
