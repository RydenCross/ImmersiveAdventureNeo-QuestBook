# Immersive Adventure Neo — Quest Book

Repository-ready FTB Quests project for Minecraft 1.21.1 NeoForge.

## Compatibility

- FTB Quests: 2101.1.27
- Quest data format: v13
- KubeJS: 2101.7.2-build.368

## Install

Copy `config/ftbquests/quests/` into the matching modpack instance folder. Back up the existing quest folder first.

In game, run `/ftbquests reload` as an operator, or restart the instance.

## Included in v0.1.0

- Eight-quest Welcome progression
- Item, advancement, and checkmark tasks
- Embedded item rewards
- Linear dependencies
- English localization
- Deterministic IDs and generator source

## Development

Edit `source/welcome.json` as the human-readable reference. `tools/generate.py` currently contains the deterministic generator used for this release.

## Important

`rewards.snbt` and `loot_crates.snbt` are intentionally empty placeholders. Rewards in this release are embedded directly in quests, matching the verified scaffold.
