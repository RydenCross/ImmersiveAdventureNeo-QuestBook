# Visual Questbook Editor Data Model

The editor model converts a generated quest blueprint into a deterministic JSON document suitable for a desktop or web-based visual editor. It separates chapter nodes, quest nodes, and prerequisite edges so a UI can render and edit the graph without parsing FTB Quests SNBT directly.

## Generate an editor document

```bash
python -m generator quest-editor-model /path/to/modpack.mrpack \
  --target-quests 600 \
  --chapter-size 40 \
  --description-style guided \
  --reward-policy conservative \
  --format json \
  --output quest-editor-model.json
```

The default reward policy is `unassigned`. Supported generated reward policies are `none`, `conservative`, `balanced`, and `generous`.

## Document structure

The JSON document contains:

- a versioned editor schema and deterministic revision number;
- pack and source metadata;
- stable chapter nodes with order and chapter prerequisites;
- stable quest nodes with objectives, coordinates, descriptions, source provenance, review state, and reward decisions;
- explicit prerequisite edges between quests;
- dirty-entity tracking and a deterministic change log;
- structural validation results.

## Editing API

`generator.editor_model` exposes immutable editor operations:

- `update_chapter` changes chapter title, category, or order;
- `update_quest` changes editable quest copy or review state;
- `move_quest` changes chapter membership or visual coordinates;
- `set_dependency` adds or removes a prerequisite edge.

Every accepted operation returns an `EditorTransaction` containing the before and after documents. `undo()` restores the exact previous document and `redo()` returns the accepted revision. Invalid operations leave the source document unchanged.

The validator rejects duplicate IDs, missing chapters, dangling edges, dependency cycles, unsupported objectives, invalid reward decisions, and non-positive counts. Coordinate collisions are reported as warnings so an editor can show them without corrupting the graph.

## Blueprint and FTB Quests compatibility

`editor_document_to_blueprint()` converts the edited document back into the existing quest blueprint format. That blueprint can continue through review and the FTB Quests SNBT exporter. The editor format therefore acts as an application layer rather than replacing the existing generator and validator pipeline.

## Contract

```bash
python -m generator editor-model-audit
python -m generator editor-model-audit \
  --format json \
  --output reports/editor-model-audit.json
```

The contract verifies deterministic generation, JSON and blueprint round trips, FTB export compatibility, revision and dirty-state tracking, reversible edits, and rejection of dangling or cyclic dependencies.
