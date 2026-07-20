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

## Required project and legal metadata

The audit requires non-empty root `LICENSE`, `README.md`, `CHANGELOG.md`, and
`pyproject.toml` files. Missing or zero-byte metadata fails the quality gate so
release archives cannot silently ship without their legal and project context.

The audit also rejects common accidental command-output files such as `tatus`,
`git-status`, and `git-status.txt`. These files typically come from a mistyped
redirection or copied terminal output and are not valid repository content.
