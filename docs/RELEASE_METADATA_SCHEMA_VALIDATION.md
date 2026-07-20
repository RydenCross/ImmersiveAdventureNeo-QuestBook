# Release Metadata Schema Validation

Before release publication, the installer validator parses every metadata document using fail-closed structural checks.

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json \
  --expected-revision "$RELEASE_SOURCE_SHA" \
  --expected-repository "https://github.com/OWNER/REPOSITORY"
```

The validator rejects malformed but syntactically valid JSON, including non-object roots, null collections, non-object entries, unsafe filenames, malformed digest maps, and invalid nested provenance structures.

Update metadata is validated semantically rather than by searching serialized JSON text. Each platform record must bind the exact installer filename, size, and SHA-256 digest, and there must be exactly one record for each staged installer.
