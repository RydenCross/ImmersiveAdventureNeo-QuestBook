# Release Report Finalization Contract

The release artifact and reproducibility reports describe the finalized repository tree, so they must remain the final two entries in report regeneration order.

Run the contract with:

```bash
python -m generator release-report-finalization-audit
```

The contract verifies that both archive-derived reports are present, occupy the final refresh positions, converge successfully, and remain byte-stable on an immediate follow-up refresh.
