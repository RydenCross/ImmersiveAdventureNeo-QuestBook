# CI Workflow Command Integrity

GitHub Actions command steps must be structurally unambiguous. A `run:` key containing a command on the same line may not be followed by additional indented shell commands; multi-command steps must use a YAML block scalar (`run: |`).

The repository security audit also confirms that the CI workflow contains the required security, formatting, test, and quality-gate commands:

```bash
python -m generator repository-security-audit --format json
```

This contract prevents a visually present command from being skipped or interpreted as invalid YAML because of indentation.
