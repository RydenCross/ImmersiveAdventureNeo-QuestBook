# Quest Content

The first generated content lives in `content/project.py`. Running:

```bash
python -m generator
```

builds a validated FTB Quests v13 tree at:

```text
output/config/ftbquests/quests/
```

The Welcome chapter currently contains nine linked quests. IDs are deterministic, so rebuilding does not break player progression merely because the files were regenerated.
