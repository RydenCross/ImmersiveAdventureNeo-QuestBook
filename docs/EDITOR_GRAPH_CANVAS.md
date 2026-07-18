# Drag-and-Drop Import and Interactive Quest Graph

Commit 98 turns the localhost editor into the first practical visual quest-making application surface. It keeps the existing scanner, planner, description, reward, review, and FTB Quests export pipeline while adding direct pack upload and graph editing in the browser.

## Start the editor

```bash
python -m generator quest-editor-serve \
  --workspace .quest-editor \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative
```

The service can start without a source and wait at the drop zone. A source path may still be provided to open or generate a questbook immediately, and another supported modpack can replace it without restarting the service.

## Import a modpack

Drop one of these files onto the import panel or choose **Import modpack**:

- Modrinth `.mrpack`
- CurseForge export `.zip`
- Prism Launcher export `.zip`
- Server pack `.zip`
- Any supported archive containing a normal `mods` directory

Before import, choose:

- target quest count, or automatic pack recommendation;
- maximum chapter size;
- concise, guided, or detailed descriptions;
- unassigned, none, conservative, balanced, or generous rewards.

The browser uploads the archive as a binary stream to:

```text
POST /api/v1/import
```

Query parameters carry generation options, while `X-File-Name` carries the percent-encoded original filename.

## Upload safety

The service:

- accepts only `.zip` and `.mrpack` filenames;
- rejects path components, control characters, empty files, and mismatched body lengths;
- limits uploads to 1 GiB;
- streams uploads rather than loading the whole archive into memory;
- stores files under `<workspace>/imports` using a SHA-256-prefixed name;
- confines all files to the configured workspace;
- inspects archives without executing mod classes or entrypoints.

## Graph canvas

The SVG canvas displays each quest as a node and every prerequisite as a directed edge. The interface supports:

- dragging a quest to save new FTB layout coordinates;
- panning the canvas and wheel zooming;
- fitting the graph back to its default viewport;
- searching titles, descriptions, and objective IDs;
- filtering to one chapter;
- selecting a quest for title, description, and review-state editing;
- linking a prerequisite by choosing **Link prerequisite**, selecting the prerequisite node, then selecting the dependent node;
- undo, redo, model save, and FTB Quests export.

All graph changes use the existing immutable editor operations. Invalid cycles, self-links, and dangling dependencies are rejected before the document changes.

## Audit

```bash
python -m generator editor-ui-audit
python -m generator editor-ui-audit \
  --format json \
  --output reports/editor-ui-audit.json
```

The contract verifies the drop interface, graph surface, drag operation, dependency linking, direct streamed import, real localhost HTTP upload, workspace confinement, and deterministic quest graph generation.
