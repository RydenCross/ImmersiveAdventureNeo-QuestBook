# Release Archive Extraction Safety Contract

The release archive extraction safety contract verifies that the deterministic ZIP can be extracted without escaping the destination or creating ambiguous filesystem entries.

It rejects absolute and parent-traversal paths, backslashes, drive-prefixed paths, normalized-name collisions, case-folding collisions, symbolic links, and special files.

Run it with:

```bash
python -m generator release-archive-extraction-safety-audit
python -m generator release-archive-extraction-safety-audit --format json --output reports/release-archive-extraction-safety-audit.json
```
