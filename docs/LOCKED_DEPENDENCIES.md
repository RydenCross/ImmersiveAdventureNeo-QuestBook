# Locked Dependencies and Hash-Verified Reproduction

Commit 114 adds a repository-level policy for deterministic Python tool environments.

`requirements-ci.lock` contains exact package versions and one or more SHA-256 artifact hashes per entry. The lock validator rejects version ranges, unpinned packages, missing hashes, duplicate package names, and malformed records.

Validate the checked-in lock:

```bash
python -m generator dependency-lock-audit --format json
```

Create a machine-readable lock manifest:

```bash
python -m generator quest-maker-lock-manifest \
  --lock requirements-ci.lock \
  --output dependency-lock-manifest.json
```

Print the hardened install plan:

```bash
python -m generator quest-maker-lock-plan --lock requirements-ci.lock
```

The generated plan uses `pip install --require-hashes --no-deps --only-binary=:all:` so dependency resolution cannot silently drift during a reproduced CI environment build.
