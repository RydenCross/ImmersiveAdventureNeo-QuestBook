# Documentation Contract Audit

```bash
python -m generator documentation-audit
python -m generator documentation-audit --format json --output reports/documentation-audit.json
```

This audit checks that every registered CLI command is documented, every local Markdown link resolves, and no tracked Markdown document is empty.
