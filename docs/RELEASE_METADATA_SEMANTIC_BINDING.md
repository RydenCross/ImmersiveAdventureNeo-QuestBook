# Release Metadata Semantic Binding

Commit 126 extends pre-publication validation beyond file-integrity checks. The release validator now parses the CycloneDX SBOM and SLSA provenance statement and proves that both documents describe the exact Windows and Linux installers staged for publication.

The SBOM must contain one file component for each installer with its exact filename and SHA-256 digest. The provenance statement must contain the same installer subjects and digests, use the in-toto Statement v1 and SLSA provenance v1 identifiers, name the checked-in release workflow, and bind both its external parameters and resolved dependency to the verified release source commit.

The release workflow supplies the already validated source revision and repository identity:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json \
  --expected-revision "$RELEASE_SOURCE_SHA" \
  --expected-repository "https://github.com/${GITHUB_REPOSITORY}"
```

Publication fails when either metadata document is malformed, omits an installer, uses a stale digest, names an unexpected subject, references another repository, names another workflow, or records a source revision different from the verified release tag commit.
