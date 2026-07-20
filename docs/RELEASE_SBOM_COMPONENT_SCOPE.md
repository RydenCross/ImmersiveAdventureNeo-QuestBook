# Release SBOM Component Scope

The publication validator treats the release CycloneDX document as an exact description of the staged installer set.

Only the two installer file components are permitted in the top-level `components` array. Arbitrary library, framework, container, operating-system, device, or unknown component rows are rejected before checksums, attestations, or release publication can be trusted.

This prevents hidden dependency injection and misleading package declarations from being smuggled into an otherwise valid, checksum-bound SBOM. Dependency inventory belongs in the repository dependency and license reports; the release SBOM is intentionally scoped to the published binary artifacts.

Run the focused validator with:

```bash
pytest -q tests/test_release_install_validation.py
```
