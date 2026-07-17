# Validation and linting

Run the validator against an FTB Quests directory:

```bash
python -m generator lint config/ftbquests/quests
```

The command exits with status `1` when validation errors are found and `0` when only warnings or no issues are present.

Current checks include duplicate chapter and quest IDs, duplicate task and reward IDs, missing or self-referencing dependencies, dependency cycles, non-finite coordinates, empty quests, and malformed resource locations.
