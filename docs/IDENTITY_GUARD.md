# Quest Identity Guard

Quest IDs are referenced by prerequisites and stored in player progression data. Accidental ID, UUID, title, or chapter-placement changes can break dependencies or make existing completion state appear lost.

Run the checked-in guard:

```bash
python -m generator identity-guard
```

Write a machine-readable report:

```bash
python -m generator identity-guard --format json --output reports/identity-guard.json
```

After an intentional, reviewed identity change, refresh the protected manifest:

```bash
python -m generator identity-baseline reports/quest-identity-baseline.json
```

The guard permits newly added chapters and quests. It fails when a protected chapter or quest disappears, or when a protected identity record changes. Protected quest records include the FTB ID, deterministic UUID, title, and chapter placement.
