# Release SBOM Identity Binding

The final desktop release validator treats the CycloneDX SBOM as a release identity document, not only as a list of installer hashes.

Before publication, it requires CycloneDX 1.5, document version 1, the `ftb-quest-maker` application component, the normalized release version, and the deterministic serial number produced from that version and the exact installer filename set. Each installer file component must also contain its exact SHA-256 digest and `ftb-quest-maker:size-bytes` property.

This prevents a validly checksummed but semantically forged SBOM from describing another application, another artifact set, or incorrect installer sizes.

Run the focused checks with:

```bash
python -m pytest tests/test_release_install_validation.py
```
