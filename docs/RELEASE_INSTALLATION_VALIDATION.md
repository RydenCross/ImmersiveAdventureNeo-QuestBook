# Release Installation Validation

Commit 120 adds a publication gate for the actual desktop artifacts produced by GitHub Actions.

Before attestation or release publication, the workflow requires exactly one Windows installer, one Linux AppImage, one CycloneDX SBOM, one SLSA provenance statement, one `update.json`, and one `SHA256SUMS`. It verifies minimum installer size, the Windows PE `MZ` signature, the Linux ELF signature and executable permission, filename/hash binding in `update.json`, and exact one-to-one SHA-256 manifest coverage for every staged file except the manifest itself.

The staged release directory is fail-closed: unexpected regular files, symbolic links, non-regular filesystem entries, duplicate basenames, missing metadata, missing checksum entries, and checksum entries for nonexistent assets all block attestation and publication. This prevents debug output, stale packages, path collisions, or untracked files from being silently included in a GitHub Release.

Run the same validation locally against staged release assets:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json
```

A failed check exits nonzero and prevents attestation and publishing.
