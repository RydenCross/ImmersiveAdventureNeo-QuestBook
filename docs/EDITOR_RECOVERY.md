# Editor Autosave and Recovery

The visual editor protects unsaved work with atomic autosave records and bounded project snapshots stored inside the configured editor workspace.

## Autosave behavior

Every accepted operation updates `.recovery/autosave.json`, including:

- individual quest or chapter edits;
- atomic bulk operations;
- automatic graph layout;
- undo and redo;
- modpack generation and browser import.

The autosave record contains the editor schema version, revision, reason, SHA-256 digest, and full editor document. Recovery validates the schema, checksum, revision, and editor graph before replacing the active session.

Saving a normal project JSON clears the active autosave because the document is no longer unsaved. Manual snapshots remain available.

## Project snapshots

The browser **Snapshot** action writes a content-addressed checkpoint under `.recovery/snapshots/`. Snapshot names contain the document revision and digest, making repeated checkpoints idempotent. The store keeps the newest 20 valid snapshots by default and prunes older records.

Before restoring over a dirty document, the current document is checkpointed as `before-restore` so recovery itself does not discard work.

## API

```text
GET  /api/v1/recovery
POST /api/v1/snapshot
POST /api/v1/recover
POST /api/v1/discard-recovery
```

Create a snapshot:

```json
{
  "reason": "before restructuring Mekanism"
}
```

Restore the latest autosave:

```json
{}
```

Restore a named snapshot:

```json
{
  "snapshot": "revision-00000042-a1b2c3d4e5f6.json"
}
```

Discard only the active autosave while keeping snapshots:

```json
{
  "keep_snapshots": true
}
```

## Validation

```bash
python -m generator editor-recovery-audit
python -m generator editor-recovery-audit \
  --format json \
  --output reports/editor-recovery-audit.json
```

The audit covers atomic autosave creation, snapshot round trips, bounded history, checksum rejection, save behavior, API routes, and browser controls.
