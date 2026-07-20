# Visual Reward and Loot Editor

The quest inspector exposes generated reward decisions instead of hiding them in the project model.

For each quest, authors can choose:

- **Unassigned** — leave reward design for later review.
- **No reward** — explicitly export the quest without a reward.
- **Custom rewards** — add one or more editable reward records.

Each reward records a type, identifier, count, and design reason. Supported authoring categories include item, XP, command, and loot rewards. Reward changes are normal editor transactions, so undo, redo, autosave, snapshots, project bundles, and FTB Quests export preserve the edited values.

The model rejects rewarded quests without reward rows, reward rows on non-rewarded quests, blank reward types or identifiers, malformed reward payloads, and counts below one.
