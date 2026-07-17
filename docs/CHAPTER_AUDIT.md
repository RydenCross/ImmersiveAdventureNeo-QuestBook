# Chapter Integrity Audit

The chapter integrity audit validates the authored chapter catalog before release.

```bash
python -m generator chapter-audit --strict
```

Write a machine-readable report with:

```bash
python -m generator chapter-audit \
  --strict \
  --format json \
  --output reports/chapter-audit.json
```

The audit verifies:

- chapter IDs follow the ordered `NN_slug` convention;
- UUIDs and FTB IDs are globally unique;
- each FTB ID matches its deterministic UUID;
- chapter titles are unique;
- icons are valid resource locations;
- descriptions are not empty;
- chapters contain at least one quest; and
- `order_index` values match the authored chapter sequence.

Use `--strict` in CI so structural chapter defects return a non-zero exit code.
