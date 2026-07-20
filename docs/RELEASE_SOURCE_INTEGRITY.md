# Release source integrity

Commit 121 prevents a release tag from naming one revision while GitHub Actions builds another. Both release jobs check out the requested tag with full history and verify that `git rev-list -n 1 <tag>` exactly matches the checked-out `HEAD` before dependencies are installed or artifacts are downloaded.

Run the same validation locally:

```bash
python -m generator.release_source_validation \
  --tag v1.2.3 \
  --source-commit "$(git rev-parse HEAD)"
```

The command rejects malformed semantic-version tags, unresolved tags, abbreviated SHAs, and any tag-to-source mismatch.
