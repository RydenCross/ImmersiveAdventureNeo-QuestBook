# Immersive Adventure Neo Quest Builder

Python toolkit for building and maintaining the FTB Quests content for **Immersive Adventure Neo**.

## Features

- FTB Quests v13 support
- Deterministic UUID generation
- Validation
- Automatic quest layout
- Localization generation
- Quest statistics
- Release packaging

## Status

🚧 Early Development
## Build the Questbook

```bash
python -m generator
```

This validates the source content and writes the generated FTB Quests v13 files to:

```text
output/config/ftbquests/quests/
```

The current playable milestone contains the nine-quest Welcome chapter.
