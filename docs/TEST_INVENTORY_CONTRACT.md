# Test Inventory Contract

The test inventory contract ensures every registered quality-gate audit has a dedicated regression test module containing at least one pytest test function.

```bash
python -m generator test-inventory-audit
python -m generator test-inventory-audit --format json --output reports/test-inventory-audit.json
```

The audit fails when a registered safeguard has no mapped test file, when the file is missing, or when it contains no `test_` functions.
