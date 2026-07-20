# Release SBOM and provenance

FTB Quest Maker can generate deterministic CycloneDX 1.5 software bills of materials and SLSA provenance statements for desktop release artifacts.

```bash
python -m generator quest-maker-release-sbom --version 1.2.3 --artifact dist/FTB-Quest-Maker.exe --artifact dist/FTB-Quest-Maker.AppImage --output dist/ftb-quest-maker-sbom.cdx.json
```

```bash
python -m generator quest-maker-release-provenance --repository https://github.com/OWNER/REPOSITORY --revision "$GITHUB_SHA" --workflow .github/workflows/publish-release.yml --artifact dist/FTB-Quest-Maker.exe --artifact dist/FTB-Quest-Maker.AppImage --output dist/ftb-quest-maker-provenance.intoto.jsonl
```

The provenance statement binds every artifact filename to its SHA-256 digest. The publishing workflow uploads both documents beside the installers and update feed. GitHub-hosted artifact attestations may be layered on top without storing signing keys in this repository.

Audit the implementation with:

```bash
python -m generator release-attestation-audit
```
