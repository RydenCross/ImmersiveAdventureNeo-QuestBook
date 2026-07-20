# Quest Text Quality Audit

Run `python -m generator text-audit --strict` to validate authored chapter and quest copy.

The audit fails on placeholder phrases, malformed whitespace or delimiters, and duplicated substantive quest descriptions. Very short descriptions are reported for review but do not fail CI.

Use JSON output for automation:

```bash
python -m generator text-audit --strict --format json --output reports/text-audit.json
```
