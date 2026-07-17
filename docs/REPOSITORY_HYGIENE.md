# Repository Hygiene Audit

The repository hygiene audit prevents accidental release of caches, build products,
credential-like files, and unusually large files.

```bash
python -m generator repository-hygiene-audit
```

Create a machine-readable report:

```bash
python -m generator repository-hygiene-audit \
  --format json \
  --output reports/repository-hygiene-audit.json
```

The audit verifies that `.gitignore` covers Python caches, virtual environments,
generated output, build directories, package metadata, environment files, and key
material. It also scans the source tree for forbidden build artifacts, secret-like
filenames, and files larger than one megabyte.

Runtime cache directories such as `__pycache__` and `.pytest_cache` are skipped during
the scan because test and CLI execution can create them locally; their required
`.gitignore` coverage is still enforced.
