# Editor Workspace Tools

Commit 99 adds deterministic graph auto-layout and atomic bulk editing to the local FTB Quest Maker.

## Automatic graph layout

Use **Auto layout** in the graph toolbar to reorganize the current chapter, or all chapters when no chapter filter is active. The layout engine:

- Computes topological progression depth from prerequisite edges.
- Places prerequisite quests to the left of dependent quests.
- Uses stable quest order and IDs for deterministic vertical placement.
- Prevents coordinate collisions inside each chapter.
- Records the entire layout as one reversible editor transaction.

The API route is:

```text
POST /api/v1/auto-layout
```

Optional JSON fields are `chapter_id`, `horizontal_spacing`, and `vertical_spacing`.

## Bulk quest editing

Hold Ctrl, Command, or Shift while selecting graph nodes or navigator entries. The toolbar can then:

- Mark all selected quests for manual review.
- Clear the manual-review flag.
- Move selected quests into another chapter.

Bulk edits are submitted through:

```text
POST /api/v1/batch-operations
```

The request contains an `operations` array using the same operation objects accepted by `/api/v1/operations`. A batch is atomic: if any operation fails validation, none of the changes are applied. A successful batch occupies one undo-history entry even when it updates hundreds of quests.

## Safety limits

A batch may contain at most 1,000 operations. Auto-layout spacing values must be between 1 and 20. Existing dependency-cycle, dangling-reference, duplicate-order, and objective validation remains active for every operation.

## Contract audit

```bash
python -m generator editor-workspace-audit
python -m generator editor-workspace-audit \
  --format json \
  --output reports/editor-workspace-audit.json
```

The contract verifies deterministic and dependency-safe layout, collision prevention, atomic rollback, one-step undo, API routing, and browser controls.
