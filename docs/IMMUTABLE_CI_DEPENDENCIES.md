# Immutable CI dependencies

All external GitHub Actions used by this repository are pinned to full 40-character commit SHAs. Version comments remain beside each pin for human review.

The repository security audit rejects mutable tags and branches in `uses:` references. Local actions (`./...`) and digest-pinned container actions are permitted.

Dependabot checks GitHub Actions weekly and proposes reviewed SHA updates. Never replace a full SHA with a floating major-version tag during review.

Run the policy locally:

```bash
python -m generator repository-security-audit --format json
```
