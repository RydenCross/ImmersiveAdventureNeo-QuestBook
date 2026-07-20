# Release Lockfile Enforcement

Commit 119 makes Windows and Linux release builds install the same hash-verified dependency lock used by continuous integration.

The release workflow installs `requirements-ci.lock` with:

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: -r requirements-ci.lock
```

The project is installed separately with `--no-deps`, so release packaging cannot silently resolve a different desktop dependency set. The dependency-lock contract rejects the former mutable `pip install .[desktop]` command in `.github/workflows/publish-release.yml`.

Run the policy locally with:

```bash
python -m generator dependency-lock-audit --format json
```
