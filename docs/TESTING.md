# In-game testing

1. Back up the existing `config/ftbquests/quests` folder.
2. Copy this repository's `config/ftbquests/quests` folder into the instance.
3. Start a temporary world with editing mode disabled.
4. Run `/ftbquests reload` or restart.
5. Confirm the Welcome chapter opens and all eight quests appear in a line.
6. Complete Oak Log, Crafting Table, Stone Age, Acquire Hardware, and Sweet Dreams naturally.
7. Confirm each reward can be claimed and each dependency unlocks correctly.
8. If parsing fails, preserve `latest.log` and the generated quest folder for diagnosis.
