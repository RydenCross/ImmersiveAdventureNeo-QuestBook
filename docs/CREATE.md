# Create chapter

The Create chapter currently contains 54 quests split into three maintainable modules:

- `content/create/foundations.py` — rotational power, stress, gearing, and early power sources.
- `content/create/processing.py` — milling, pressing, mixing, crushing, and fan processing.
- `content/create/automation.py` — belts, funnels, filtered logistics, deployers, sequenced assembly, precision mechanisms, arms, and vaults.

The chapter unlocks after the Mining completion quest. Each section returns a completion quest ID so the next section can depend on it without coupling modules to generated IDs.
