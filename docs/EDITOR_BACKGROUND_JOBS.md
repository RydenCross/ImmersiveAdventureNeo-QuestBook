# Editor Background Generation Jobs

Large modpacks can require enough recipe, advancement, registry, description, and reward analysis that a single browser request would appear frozen. The local editor therefore runs imported-pack generation as an observable in-process background job.

## Browser workflow

Start the local editor normally:

```bash
python -m generator quest-editor-serve --workspace .quest-editor
```

Drop a `.mrpack` or `.zip` file into the browser. The upload is stored first, then the editor immediately receives a job identifier. A progress panel reports the current stage and percentage while the existing questbook remains available. The active document is replaced only after the new document passes structural validation.

The browser exposes a **Cancel** button. Cancellation is cooperative and is checked between the expensive scan, planning, description, reward, and editor-model stages. A cancelled or failed job never partially replaces the current document.

## Generation stages

Background generation reports these stable stages:

1. `pack-profile` — loader, Minecraft version, and mod inventory
2. `content-scan` — recipes, advancements, tags, and registries
3. `progression` — quest selection, chapters, and dependencies
4. `descriptions` — grounded player instructions
5. `rewards` — optional reward decisions
6. `editor-model` — final graph construction and validation

Progress is monotonic. Completed jobs report 100 percent.

## API

Queue an already uploaded workspace path:

```text
POST /api/v1/generate-job
```

```json
{
  "path": "imports/example.mrpack",
  "target_quests": 600,
  "chapter_size": 40,
  "description_style": "guided",
  "reward_policy": "conservative"
}
```

Stream and queue a new archive:

```text
POST /api/v1/import-job
```

The import endpoint uses the same query parameters as the synchronous import route and requires `X-File-Name` plus an exact `Content-Length`.

Inspect retained jobs:

```text
GET /api/v1/jobs
GET /api/v1/jobs/{job-id}
```

Cancel active work:

```text
POST /api/v1/jobs/{job-id}/cancel
```

Job payloads include the state, stage, progress percentage, message, cancellability, result summary, and error text. States are `queued`, `running`, `completed`, `failed`, and `cancelled`.

The service retains a bounded recent job history and uses daemon worker threads so local shutdown is not blocked by abandoned browser sessions.

## Validation

```bash
python -m generator editor-jobs-audit
python -m generator editor-jobs-audit \
  --format json \
  --output reports/editor-jobs-audit.json
```

The contract verifies staged progress, background imports, atomic replacement, cooperative cancellation, failure isolation, API routes, and browser progress controls.
