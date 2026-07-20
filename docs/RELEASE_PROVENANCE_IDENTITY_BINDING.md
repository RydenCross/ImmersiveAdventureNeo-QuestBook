# Release Provenance Identity Binding

Commit 128 strengthens pre-publication SLSA provenance validation. A valid statement must identify the GitHub Actions workflow v1 build type, the GitHub Actions runner builder, exactly one resolved dependency bound to both the expected repository URI and verified Git commit, and an invocation identifier derived from the repository, revision, and release workflow.

Run the complete release validation with:

```bash
python -m generator.release_install_validation \
  --assets release-assets \
  --checksums release-assets/SHA256SUMS \
  --update release-assets/update.json \
  --expected-revision "$RELEASE_SOURCE_SHA" \
  --expected-repository "https://github.com/OWNER/REPOSITORY"
```

Publication fails when any provenance identity field is missing, forged, duplicated, or inconsistent.
