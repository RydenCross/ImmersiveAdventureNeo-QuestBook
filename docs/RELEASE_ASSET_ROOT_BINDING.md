# Release Asset Root Binding

Release publication validates one flat, self-contained `release-assets` directory.

The installer validator requires every regular release file to be stored directly in
that directory. Nested allowlisted files are rejected even when their basenames are
otherwise valid. The `--checksums` and `--update` arguments must resolve to the exact
`release-assets/SHA256SUMS` and `release-assets/update.json` files, preventing an
external or substituted metadata file from being used to validate a different asset
set.

Run the validation before attestation or publication:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json
```
