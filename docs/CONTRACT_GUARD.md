# Quest Contract Guard

The quest contract guard protects the gameplay-facing shape of existing quests while allowing normal prose edits and new quests.

It records each protected quest's icon, difficulty, optional/hidden/repeatable flags, task IDs and task types, and reward IDs and reward types.

```bash
python -m generator contract-guard
python -m generator contract-guard --format json --output reports/contract-guard.json
```

After an intentional reviewed contract change, refresh the baseline:

```bash
python -m generator contract-baseline reports/quest-contract-baseline.json
```

Adding new quests does not fail the guard. Removing a protected quest or changing its protected gameplay contract does.
