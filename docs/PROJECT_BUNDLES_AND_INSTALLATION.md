# Portable project bundles and installation

FTB Quest Maker can package the current editor document, source fingerprint, generation settings, and validated FTB Quests export into one deterministic `.ftbqproj` file.

```bash
python -m generator quest-project-bundle /path/to/modpack.mrpack \
  --destination shared.ftbqproj \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative
```

Verify a shared bundle before opening or installing it:

```bash
python -m generator quest-project-inspect shared.ftbqproj
```

Install it into a Minecraft instance:

```bash
python -m generator quest-project-install shared.ftbqproj /path/to/instance
```

The installer writes to `config/ftbquests`, validates the bundled SNBT before replacement, preserves the previous questbook under `.quest-maker-backups/`, rejects symlink destinations, and checks detected Minecraft/loader compatibility. Use `--dry-run` to preview or `--force` to accept an explicit platform mismatch.

The local browser editor accepts `.ftbqproj` files through the same drop zone and exposes `/api/v1/project-bundle-import`, `/api/v1/bundle`, `/api/v1/open-bundle`, and `/api/v1/install` routes plus **Save project bundle** and **Install to instance** controls.

Validate the feature with:

```bash
python -m generator project-bundle-audit
python -m generator project-bundle-audit --format json --output reports/project-bundle-audit.json
```
