# Keyless release signing and attestation verification

Commit 110 adds release checksums and GitHub artifact attestations without storing a private signing key in the repository.

Generate a deterministic checksum manifest:

```bash
python -m generator quest-maker-release-checksums \
  --artifact dist/FTB-Quest-Maker.exe \
  --artifact dist/FTB-Quest-Maker.AppImage \
  --output dist/SHA256SUMS
```

Create a safe verification plan:

```bash
python -m generator quest-maker-release-verify-attestations \
  --repository OWNER/REPOSITORY \
  --artifact dist/FTB-Quest-Maker.exe \
  --artifact dist/FTB-Quest-Maker.AppImage
```

Add `--execute` to invoke `gh attestation verify` for every artifact. The GitHub release workflow uses `actions/attest@v4` with short-lived OIDC credentials and uploads `SHA256SUMS` with the release assets.

Audit the complete contract:

```bash
python -m generator release-signing-audit
```
