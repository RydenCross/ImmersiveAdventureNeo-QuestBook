# Release metadata uniqueness

Commit 127 removes duplicate-entry ambiguity from pre-publication metadata validation.

Each staged installer must appear exactly once as a CycloneDX file component and exactly once as an in-toto provenance subject. Every entry must contain one canonical lowercase SHA-256 digest. Duplicate names, repeated SHA-256 declarations, uppercase or malformed digests, and duplicate source dependencies are rejected before attestation or publication.

Run the validator through the release workflow or directly:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json \
  --expected-revision "$RELEASE_SOURCE_SHA" \
  --expected-repository "https://github.com/OWNER/REPOSITORY"
```
