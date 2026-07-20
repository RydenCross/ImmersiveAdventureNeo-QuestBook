# Release Guard and Safe Baseline Refresh

The release guard prevents accidental questbook regressions by comparing a fresh
`release-check` report with the checked-in baseline at
`reports/release-baseline.json`.

## Check the current repository

```bash
python -m generator release-guard
```

The command fails when release validation fails or when content/quality metrics
regress relative to the baseline.

A JSON report can be written for CI:

```bash
python -m generator release-guard --format json --output reports/release-guard.json
```

## Safely refresh the baseline

```bash
python -m generator release-baseline reports/release-baseline.json
```

The refresh command first runs the complete release check. It refuses to create
or overwrite the baseline if that check is not clean, and creates missing parent
directories automatically.

Refresh the baseline only when an intentional, reviewed content change should
become the new minimum release state.
