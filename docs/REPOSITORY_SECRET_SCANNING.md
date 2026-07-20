# Repository Secret Scanning and Workflow Permission Policy

Commit 112 adds a dependency-free repository security scanner that detects private-key blocks and common high-confidence service-token formats before changes are committed or released. The scanner reports only the file, line, and secret class; it never echoes the matching credential value.

Run the policy locally:

```bash
python -m generator quest-maker-secret-scan --format json
python -m generator repository-security-audit --format json --output reports/repository-security-audit.json
```

Use `--exclude PATH` only for reviewed fixture directories or intentionally synthetic files. Exclusions are explicit, portable repository-relative paths.

The policy also validates GitHub Actions workflows. CI must use top-level `contents: read`; release publishing must declare only the write permissions required for releases and keyless attestations. Broad `write-all`, `read-all`, and `pull_request_target` workflows are rejected.
