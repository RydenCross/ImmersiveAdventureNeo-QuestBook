# Release Installation Validation

Commit 120 adds a publication gate for the actual desktop artifacts produced by GitHub Actions.

Before attestation or release publication, the workflow now requires exactly one Windows installer and one Linux AppImage. It verifies minimum file size, the Windows PE `MZ` signature, the Linux ELF signature and executable permission, SHA-256 consistency with `SHA256SUMS`, and filename/hash binding in `update.json`.

Run the same validation locally against staged release assets:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json
```

A failed check exits nonzero and prevents attestation and publishing.
