# Release Version Identity Binding

The desktop release workflow accepts a Git tag such as `v1.2.3`, verifies that tag against the checked-out source revision, and derives the normalized package version `1.2.3` exactly once. The normalized value is exported as `RELEASE_VERSION`.

The workflow uses `RELEASE_VERSION` for update metadata and CycloneDX SBOM generation. The final release installer validator receives the same value through `--expected-version` and rejects publication unless both `update.json` and the SBOM application component declare that exact version.

This prevents a release from publishing correctly checksummed installers alongside metadata for a different release version.

Run the focused validation tests with:

```bash
python -m pytest tests/test_release_install_validation.py tests/test_release_attestation_contract.py
```
