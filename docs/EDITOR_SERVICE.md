# Local Visual Editor Service and API

The local editor service turns the versioned editor data model into a dependency-free browser application and JSON API. It binds to a loopback address only, so the editor remains local to the machine running the generator.

## Start the editor

```bash
python -m generator quest-editor-serve /path/to/modpack.mrpack \
  --workspace .quest-editor \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative
```

The command prints a local URL, opens it in the default browser, and serves the editor until `Ctrl+C` is pressed. Use `--no-browser` to suppress automatic browser launch. An existing editor JSON document can be supplied instead of a modpack.

The service defaults to `127.0.0.1:8765`. It rejects non-loopback bindings. Use `--port 0` to select an available local port automatically.

## Browser interface

The built-in interface provides:

- chapter and quest browsing;
- quest title and description editing;
- validated operation submission;
- undo and redo controls;
- editor-model save actions;
- direct FTB Quests SNBT export.

The interface uses the same API exposed to a future richer desktop or web frontend.

## JSON API

All API routes use the `/api/v1` prefix.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/status` | Session revision, history, counts, and dirty state |
| `GET` | `/document` | Complete editor document |
| `GET` | `/validation` | Current graph validation result |
| `POST` | `/operations` | Apply an `update_chapter`, `update_quest`, `move_quest`, or `set_dependency` operation |
| `POST` | `/undo` | Restore the previous accepted document |
| `POST` | `/redo` | Reapply an undone document |
| `POST` | `/save` | Save editor JSON inside the workspace |
| `POST` | `/open` | Open editor JSON inside the workspace |
| `POST` | `/generate` | Generate a new model from a pack located inside the workspace |
| `POST` | `/export` | Export the current document as FTB Quests SNBT inside the workspace |

Example operation:

```json
{
  "action": "update_quest",
  "target_id": "quest:create:mechanical_press",
  "values": {
    "title": "Build a Mechanical Press",
    "description": "Craft and place a Mechanical Press to begin automated processing."
  }
}
```

## File safety

Save, open, generate, and export paths received through the API are resolved beneath the configured workspace. Parent traversal, absolute paths outside the workspace, and symlink escapes are rejected. Request bodies are limited to one MiB.

## Contract

```bash
python -m generator editor-service-audit
python -m generator editor-service-audit \
  --format json \
  --output reports/editor-service-audit.json
```

The contract verifies session generation, validated edits, undo/redo history, save/open round trips, workspace confinement, loopback-only binding, HTTP routing, deterministic documents, and FTB Quests export.

## Browser modpack import

`POST /api/v1/import` accepts a streamed `.zip` or `.mrpack` body. Supply the percent-encoded original filename in `X-File-Name`; optional query parameters are `target_quests`, `chapter_size`, `description_style`, and `reward_policy`. Uploads are limited to 1 GiB, written inside `<workspace>/imports`, named with a SHA-256 prefix, and scanned without executing mod code.
