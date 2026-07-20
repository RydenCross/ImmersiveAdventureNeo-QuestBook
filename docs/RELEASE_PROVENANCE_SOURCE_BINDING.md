# Release provenance source binding

Commit 122 binds SLSA provenance to the exact checked-out commit already validated against the requested release tag.

The release workflow resolves `git rev-parse HEAD` once, validates that full SHA against the tag, exports it as `RELEASE_SOURCE_SHA`, and passes that same value to `quest-maker-release-provenance`. It must not use the workflow-dispatch `${{ github.sha }}` context because that value can identify the default-branch workflow revision instead of the tagged source being packaged.

Run the contract locally:

```bash
python -m generator release-attestation-audit
```

A release fails the contract if provenance is not generated from `$RELEASE_SOURCE_SHA` or if `${{ github.sha }}` is used by the publishing workflow.
