# CI Lockfile Enforcement

Commit 118 makes the continuous-integration environment use the same hash-verified dependency lock that the repository audits.

The CI workflow installs `requirements-ci.lock` with:

```bash
python -m pip install --require-hashes --no-deps --only-binary=:all: -r requirements-ci.lock
```

The project itself is installed separately with `--no-deps`, preventing project metadata from silently resolving newer dependency versions. The dependency-lock contract rejects a return to the former mutable `pip install .[dev,desktop] pip-audit` command.

Run the policy locally with:

```bash
python -m generator dependency-lock-audit --format json
```
