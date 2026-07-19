# Immersive Adventure Neo Quest Builder

A deterministic Python authoring toolkit and generated FTB Quests v13 questbook for **Immersive Adventure Neo** on Minecraft 1.21.1/NeoForge.

## Current questbook

- 13 chapters
- 656 quests
- 223 optional quests
- Welcome, Survival, Mining, Exploration
- Create and Create Addons
- Actually Additions
- Ars Nouveau
- Apotheosis
- Applied Energistics 2
- Mekanism
- Endgame and Challenges

## Modpack scanner and pack profile

Scan a Modrinth, CurseForge, Prism, server-pack, instance, or plain `mods` input without executing mod code:

```bash
python -m generator modpack-scan /path/to/modpack.mrpack
python -m generator modpack-scan /path/to/instance --format json --output pack-profile.json
```

The profile records the Minecraft/loader versions, normalized mod inventory, content-versus-library classification, gameplay categories, unresolved remote references, and a recommended quest-count range for the future generic quest generator.

Validate the scanner itself with:

```bash
python -m generator modpack-scanner-audit
python -m generator modpack-scanner-audit --format json --output reports/modpack-scanner-audit.json
```

See [`docs/MODPACK_SCANNER.md`](docs/MODPACK_SCANNER.md).

## Recipe, advancement, and registry scanner

Turn a scanned pack into progression-ready quest candidates without launching Minecraft:

```bash
python -m generator modpack-content-scan /path/to/modpack.mrpack
python -m generator modpack-content-scan /path/to/instance \
  --candidate-limit 600 \
  --format json \
  --output quest-candidates.json
```

The scanner reads recipes, advancements, item registries, tags, and English names from mod JARs and bundled datapacks. It creates deterministic candidate titles, objectives, prerequisite edges, confidence scores, and broad per-mod coverage.

Validate the content scanner with:

```bash
python -m generator modpack-content-scanner-audit
python -m generator modpack-content-scanner-audit --format json --output reports/modpack-content-scanner-audit.json
```

See [`docs/MODPACK_CONTENT_SCANNER.md`](docs/MODPACK_CONTENT_SCANNER.md).

## Progression planner and quest blueprint

Turn scanned candidates into ordered mod chapters and a reviewable questbook blueprint:

```bash
python -m generator quest-blueprint /path/to/modpack.mrpack
python -m generator quest-blueprint /path/to/modpack.mrpack \
  --target-quests 600 \
  --chapter-size 40 \
  --format json \
  --output quest-blueprint.json
```

The planner preserves prerequisite closure, balances selection across mods, splits oversized chapters, creates deterministic layout coordinates, records cross-chapter requirements, and flags low-confidence registry-only quests for review. It reports a candidate shortfall rather than inventing unsupported objectives.

Validate the planner with:

```bash
python -m generator progression-planner-audit
python -m generator progression-planner-audit --format json --output reports/progression-planner-audit.json
```

See [`docs/PROGRESSION_PLANNER.md`](docs/PROGRESSION_PLANNER.md).

## Quest description and instruction generation

Replace short scanner copy with grounded player-facing instructions before reward planning or export:

```bash
python -m generator quest-description-plan /path/to/modpack.mrpack \
  --target-quests 600 \
  --style guided \
  --format json \
  --output quest-description-plan.json
```

The generator explains item and advancement completion, names prerequisite quests, lists known inputs and accepted tags, describes generated unlocks, and adds explicit review guidance for registry-only objectives. It does not invent unconfirmed machines or processing methods.

Validate the generator with:

```bash
python -m generator quest-description-audit
python -m generator quest-description-audit --format json --output reports/quest-description-audit.json
```

See [`docs/QUEST_DESCRIPTION_GENERATOR.md`](docs/QUEST_DESCRIPTION_GENERATOR.md).

## Visual questbook editor data model

Generate a versioned JSON graph for a future desktop or web editor:

```bash
python -m generator quest-editor-model /path/to/modpack.mrpack \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative \
  --format json \
  --output quest-editor-model.json
```

The editor document separates chapters, quests, and prerequisite edges; preserves source, objective, layout, description, review, and reward data; and supports revisioned reversible operations with structural validation. It converts back into the existing quest blueprint for review and FTB Quests export.

Validate the model with:

```bash
python -m generator editor-model-audit
python -m generator editor-model-audit --format json --output reports/editor-model-audit.json
```

See [`docs/EDITOR_MODEL.md`](docs/EDITOR_MODEL.md).

## Desktop launcher and automatic instance discovery

Open the visual application without manually starting the localhost service or typing an instance path:

```bash
python -m generator quest-maker-launch
```

The launcher automatically discovers Minecraft Launcher, CurseForge, Prism Launcher, MultiMC, Modrinth App, ATLauncher, and GDLauncher instances. It shows detected Minecraft/loader metadata, mod counts, and existing FTB Quests installations; selected instances can be opened in the editor or receive a verified `.ftbqproj` installation directly.

List the same instances from the command line:

```bash
python -m generator quest-instance-discover
python -m generator quest-instance-discover --format json --output instances.json
```

Validate launcher discovery with:

```bash
python -m generator desktop-launcher-audit
python -m generator desktop-launcher-audit --format json --output reports/desktop-launcher-audit.json
```

See [`docs/DESKTOP_LAUNCHER_AND_INSTANCE_DISCOVERY.md`](docs/DESKTOP_LAUNCHER_AND_INSTANCE_DISCOVERY.md).

## Native desktop distribution and first-run setup

Complete persistent setup from the command line or use the first-run graphical wizard:

```bash
python -m generator quest-maker-setup --workspace ~/.ftb-quest-maker
python -m generator quest-maker-launch --reset-setup
```

Inspect or build standalone Windows/Linux desktop distributions:

```bash
python -m generator quest-maker-native-build --platform windows --dry-run
python -m generator quest-maker-native-build --platform linux --dry-run
python -m generator quest-maker-native-build --platform auto
```

The packaged `FTBQuestMaker` entrypoint opens the desktop launcher directly. Preferences are written atomically, invalid settings recover safely, the last opened instance is remembered, and native builds are restricted to their target operating system. See `docs/NATIVE_DESKTOP_DISTRIBUTION.md` for build recipes and first-run behavior.

Validate the setup and packaging surface:

```bash
python -m generator native-distribution-audit
python -m generator native-distribution-audit --format json --output reports/native-distribution-audit.json
```

## Desktop installers and application updates

Turn the target-specific native binary into a Windows installer or Linux AppImage:

```bash
python -m generator quest-maker-package-build --platform windows --version 1.0.0 --dry-run
python -m generator quest-maker-package-build --platform linux --version 1.0.0 --dry-run
```

Generate deterministic update metadata and verify its package checksums:

```bash
python -m generator quest-maker-update-metadata \
  --version 1.0.0 \
  --channel stable \
  --artifact windows=dist/packages/FTBQuestMaker-1.0.0-Setup.exe \
  --artifact linux=dist/packages/FTBQuestMaker-1.0.0-x86_64.AppImage \
  --destination dist/updates/latest.json
python -m generator quest-maker-update-verify \
  dist/updates/latest.json \
  --artifact-directory dist/packages
```

Optional HMAC-SHA256 authentication is supported through a local `--signing-key`; release keys are never stored in the repository. Validate the installer, AppImage, metadata, signature, and tamper-detection surface with:

```bash
python -m generator desktop-packages-audit
python -m generator desktop-packages-audit --format json --output reports/desktop-packages-audit.json
```

See [`docs/DESKTOP_INSTALLERS_AND_UPDATES.md`](docs/DESKTOP_INSTALLERS_AND_UPDATES.md).

## Secure update checks and staged downloads

Check a local or HTTPS release feed without installing anything:

```bash
python -m generator quest-maker-update-check \
  https://updates.example.invalid/stable/latest.json \
  --current-version 1.0.0 \
  --channel stable \
  --platform auto
```

Download only the selected platform artifact, verify its declared size and SHA-256, and move it atomically into the update staging directory:

```bash
python -m generator quest-maker-update-stage \
  https://updates.example.invalid/stable/latest.json \
  --current-version 1.0.0 \
  --channel stable \
  --destination ~/.ftb-quest-maker/updates
```

Remote metadata and artifacts must use HTTPS. Signed feeds can be verified with `--signing-key`, and `--require-signature` rejects unsigned metadata. Staging never executes installers or replaces the running application; it writes a deterministic `pending-update.json` manifest for an explicit later installation step.

Validate the update client with:

```bash
python -m generator application-update-client-audit
python -m generator application-update-client-audit \
  --format json \
  --output reports/application-update-client-audit.json
```

See [`docs/APPLICATION_UPDATE_CLIENT.md`](docs/APPLICATION_UPDATE_CLIENT.md).

## Local visual editor service and API

Launch the generated editor model as a local browser application:

```bash
python -m generator quest-editor-serve /path/to/modpack.mrpack \
  --workspace .quest-editor \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative
```

The dependency-free service binds only to localhost and provides a built-in quest editor plus versioned JSON endpoints for document inspection, validated graph operations, undo/redo, save/open, validation, regeneration, and FTB Quests export. All API-managed files are confined to the configured workspace.

Validate the service with:

```bash
python -m generator editor-service-audit
python -m generator editor-service-audit --format json --output reports/editor-service-audit.json
```

## Drag-and-drop import and interactive quest graph

The local editor now accepts CurseForge ZIPs, Modrinth `.mrpack` files, Prism exports, and server-pack archives directly in the browser. Drop a pack onto the import panel or use **Import modpack**, choose the target quest count, chapter size, description style, and reward policy, and the current editor document is replaced with the newly generated graph.

The graph canvas renders prerequisite edges and supports node selection, drag-to-move layout editing, zoom, pan, search, chapter filtering, and validated prerequisite linking. Uploaded files are streamed into the configured workspace, content-addressed by SHA-256, size-limited, and never executed.

Validate the import and canvas contract with:

```bash
python -m generator editor-ui-audit
python -m generator editor-ui-audit --format json --output reports/editor-ui-audit.json
```

See [the interactive editor guide](docs/EDITOR_GRAPH_CANVAS.md).

## Graph auto-layout and bulk editing

Large generated questbooks can now be reorganized without editing one node at a time. Use **Auto layout** to place prerequisites before dependent quests with deterministic collision-free coordinates. Ctrl/Command/Shift-select multiple quests to flag or clear manual review in bulk, or move the selection into another chapter as one atomic undoable transaction.

Validate the workspace tools with:

```bash
python -m generator editor-workspace-audit
python -m generator editor-workspace-audit --format json --output reports/editor-workspace-audit.json
```

See [`docs/EDITOR_WORKSPACE_TOOLS.md`](docs/EDITOR_WORKSPACE_TOOLS.md).

See [`docs/EDITOR_SERVICE.md`](docs/EDITOR_SERVICE.md).

## Generated quest reward planning

Assign deterministic reward drafts or explicit no-reward decisions before export:

```bash
python -m generator quest-reward-plan /path/to/modpack.mrpack \
  --target-quests 600 \
  --policy conservative \
  --format json \
  --output quest-reward-plan.json
```

Policies range from `none` through `generous`. Low-confidence quests are protected from automatic rewards, while every quest receives an explicit decision that the review report can validate.

Validate the planner with:

```bash
python -m generator reward-planner-audit
python -m generator reward-planner-audit --format json --output reports/reward-planner-audit.json
```

See [`docs/REWARD_PLANNER.md`](docs/REWARD_PLANNER.md).

## FTB Quests SNBT blueprint export

Generate a blueprint and write it directly as an installable FTB Quests v13 tree:

```bash
python -m generator ftb-quest-export /path/to/modpack.mrpack \
  --destination generated/ftbquests \
  --target-quests 600 \
  --chapter-size 40 \
  --description-style guided \
  --reward-policy conservative
```

The exporter converts item and advancement objectives into FTB tasks, assigns stable FTB IDs, preserves prerequisites across chapters, removes stale generated chapter files, reparses the emitted SNBT, and reports a deterministic tree checksum.

Validate the exporter with:

```bash
python -m generator ftb-blueprint-exporter-audit
python -m generator ftb-blueprint-exporter-audit --format json --output reports/ftb-blueprint-exporter-audit.json
```

See [`docs/FTB_BLUEPRINT_EXPORTER.md`](docs/FTB_BLUEPRINT_EXPORTER.md).

## Generated questbook review

Review a generated blueprint before installing or publishing it:

```bash
python -m generator questbook-review /path/to/modpack.mrpack \
  --target-quests 600 \
  --description-style guided \
  --reward-policy conservative \
  --format json \
  --output questbook-review.json
```

The report identifies blocking dependency or objective defects and surfaces editorial work such as low-confidence quests, weak descriptions, missing reward decisions, oversized chapters, duplicate objectives, progression bottlenecks, and target shortfalls. A clean report may still require review; `publish_ready` is only true when no warnings or review items remain.

Validate the reviewer with:

```bash
python -m generator questbook-review-audit
python -m generator questbook-review-audit --format json --output reports/questbook-review-audit.json
```

See [`docs/QUESTBOOK_REVIEW.md`](docs/QUESTBOOK_REVIEW.md).

## Build

```bash
python -m generator
```

Generated files are written to:

```text
output/config/ftbquests/quests/
```

## Validate generated SNBT

```bash
python -m generator lint output/config/ftbquests/quests
```

## Audit authored content

```bash
python -m generator audit --strict
```

The audit summarizes chapter and quest totals, optional quests, task and reward coverage, empty descriptions, taskless quests, and duplicate titles.

## Verify item IDs against installed mods

```bash
python -m generator registry-audit /path/to/instance/mods --strict
```

The registry audit checks chapter icons, quest icons, item tasks, and item rewards against mod JAR assets or JSON registry exports. It supports text or JSON reports and can write directly to a file.

```bash
python -m generator registry-audit /path/to/instance/mods --format json --output reports/registry.json
python -m generator registry-manifest --output reports/quest-item-manifest.json
```

See [`docs/REGISTRY_AUDIT.md`](docs/REGISTRY_AUDIT.md) for supported formats and limitations.

## Run the complete release gate

```bash
python -m generator release-check
```

This builds the questbook in a temporary directory, reparses and validates the generated SNBT, runs the authored-content audit, and verifies registry-manifest totals. Use `--output <directory>` to keep the generated files. Use `--format json --report-output reports/release-check.json` to create a machine-readable release record.

## Compare release reports

```bash
python -m generator release-compare reports/baseline.json reports/current.json --strict
```

This detects new validation or content-quality defects, authored/generated mismatches, and unexpected decreases in questbook or registry-manifest totals. See [`docs/RELEASE_COMPARISON.md`](docs/RELEASE_COMPARISON.md).

## Test

```bash
pytest -q
```

The repository uses deterministic IDs, cross-chapter dependency checks, generated-file regression tests, and validator coverage to keep the questbook stable as content evolves.


## Quest dependency audit

Validate progression cycles, reachability, duplicate prerequisites, and chapter entry paths:

```bash
python -m generator dependency-audit --strict
```

Machine-readable reports are supported; see [`docs/DEPENDENCY_AUDIT.md`](docs/DEPENDENCY_AUDIT.md).

### Progression graph export

```bash
python -m generator dependency-graph --output reports/dependency-graph.dot
python -m generator dependency-graph --format json --output reports/dependency-graph.json
```

See [`docs/DEPENDENCY_GRAPH.md`](docs/DEPENDENCY_GRAPH.md).

## Progression metrics

Measure critical-path depth, high fan-out bottlenecks, and cross-chapter routes:

```bash
python -m generator progression-metrics
python -m generator progression-metrics --format json --output reports/progression-metrics.json
```

Protect progression complexity with checked-in limits:

```bash
python -m generator progression-guard
python -m generator progression-guard --format json --output reports/progression-guard.json
```

See [`docs/PROGRESSION_METRICS.md`](docs/PROGRESSION_METRICS.md).

## Release baseline guard

Protect release quality and content totals against the checked-in baseline:

```bash
python -m generator release-guard
```

After an intentional reviewed change, safely refresh the baseline:

```bash
python -m generator release-baseline reports/release-baseline.json
```

See `docs/RELEASE_GUARD.md` for details.

## Quest identity guard

Protect stable chapter and quest identities against accidental removals, renames, UUID changes, or chapter moves:

```bash
python -m generator identity-guard
python -m generator identity-guard --format json --output reports/identity-guard.json
```

After an intentional reviewed identity change, refresh the protected manifest:

```bash
python -m generator identity-baseline reports/quest-identity-baseline.json
```

See [`docs/IDENTITY_GUARD.md`](docs/IDENTITY_GUARD.md).

## Quest contract guard

Protect gameplay-facing quest contracts from accidental edits while allowing description and localization improvements:

```bash
python -m generator contract-guard
python -m generator contract-guard --format json --output reports/contract-guard.json
```

Refresh the baseline only after an intentional reviewed contract change:

```bash
python -m generator contract-baseline reports/quest-contract-baseline.json
```


## Reward integrity audit

Validate reward IDs and definitions before release:

```bash
python -m generator reward-audit --strict
python -m generator reward-audit --format json --output reports/reward-audit.json
```

See [`docs/REWARD_AUDIT.md`](docs/REWARD_AUDIT.md) for the validation rules.

## Task integrity audit

Validate completion-task IDs, required task data, and task coverage before release:

```bash
python -m generator task-audit --strict
python -m generator task-audit --strict --format json --output reports/task-audit.json
```

See [`docs/TASK_AUDIT.md`](docs/TASK_AUDIT.md) for the validation rules.

## Chapter integrity audit

Validate chapter identities, metadata, ordering, and quest coverage before release:

```bash
python -m generator chapter-audit --strict
python -m generator chapter-audit --strict --format json --output reports/chapter-audit.json
```

See [`docs/CHAPTER_AUDIT.md`](docs/CHAPTER_AUDIT.md) for the validation rules.



## Quest text quality audit

Run `python -m generator text-audit --strict` to detect placeholder copy, malformed formatting, duplicated substantive descriptions, and short descriptions that deserve review. See `docs/TEXT_AUDIT.md`.


## Build determinism audit

Verify that two isolated builds produce exactly the same files and bytes:

```bash
python -m generator determinism-audit --strict
python -m generator determinism-audit --strict --format json --output reports/determinism-audit.json
```

See [`docs/DETERMINISM_AUDIT.md`](docs/DETERMINISM_AUDIT.md).


## Generated output manifest guard

Protect the exact generated FTB Quests file set and contents:

```bash
python -m generator output-manifest-guard
python -m generator output-manifest-guard --format json --output reports/output-manifest-guard.json
```

Refresh the checked-in manifest after an intentional deterministic output change:

```bash
python -m generator output-manifest reports/generated-output-manifest.json
```

See [`docs/OUTPUT_MANIFEST.md`](docs/OUTPUT_MANIFEST.md).

## Incremental report refresh

Regenerate tracked reports while skipping renderers whose source inputs and checked-in outputs are unchanged:

```bash
python -m generator report-refresh --incremental
python -m generator report-refresh --incremental --cache reports/.report-refresh-cache.json --format json
```

Validate cache population, selective invalidation, tamper recovery, and corrupt-cache recovery:

```bash
python -m generator report-refresh-cache-audit
python -m generator report-refresh-cache-audit --format json --output reports/report-refresh-cache-audit.json
```

See [`docs/REPORT_REFRESH_CACHE_CONTRACT.md`](docs/REPORT_REFRESH_CACHE_CONTRACT.md).

### Report freshness guard

Verify that checked-in audit evidence still matches the current questbook:

```bash
python -m generator report-freshness-guard --format json \
  --output reports/report-freshness-guard.json
```

See [docs/REPORT_FRESHNESS.md](docs/REPORT_FRESHNESS.md).


## Unified quality gate

Run every repository-safe release safeguard in one CI-friendly command:

```bash
python -m generator quality-gate
python -m generator quality-gate --format json --output reports/quality-gate.json
```

See [`docs/QUALITY_GATE.md`](docs/QUALITY_GATE.md).


## Packaging audit

Run `python -m generator packaging-audit` to verify package discovery and the installed console command.

### CLI contract audit

Use the CLI contract audit to ensure every supported subcommand remains registered, documented with help text, and available through the installed console entry point:

```bash
python -m generator cli-audit
python -m generator cli-audit --format json --output reports/cli-audit.json
```


## Documentation contract audit

```bash
python -m generator documentation-audit
python -m generator documentation-audit --format json --output reports/documentation-audit.json
```

See [`docs/DOCUMENTATION_AUDIT.md`](docs/DOCUMENTATION_AUDIT.md).


## Repository hygiene audit

Detect caches, build artifacts, secret-like files, and oversized accidental additions:

```bash
python -m generator repository-hygiene-audit
python -m generator repository-hygiene-audit --format json --output reports/repository-hygiene-audit.json
python -m generator release-artifact-audit
python -m generator release-artifact-audit --format json --output reports/release-artifact-audit.json
```

See [`docs/REPOSITORY_HYGIENE.md`](docs/REPOSITORY_HYGIENE.md).


## Release reproducibility audit

```bash
python -m generator release-reproducibility-audit
```

Compares two independently created release archives by normalized entry names and SHA-256 content digests.

### Audit registry contract

Verify that every release safeguard is consistently registered across the CLI, unified quality gate, and report freshness inventory:

```bash
python -m generator audit-registry-audit
```

See [docs/AUDIT_REGISTRY_CONTRACT.md](docs/AUDIT_REGISTRY_CONTRACT.md) for details.


### Test inventory contract

Verify every registered quality safeguard has direct pytest coverage:

```bash
python -m generator test-inventory-audit
python -m generator test-inventory-audit --format json --output reports/test-inventory-audit.json
```

See [docs/TEST_INVENTORY_CONTRACT.md](docs/TEST_INVENTORY_CONTRACT.md).


### Report schema contract

Validate that every registered audit report is a JSON object with a stable pass/fail status field:

```bash
python -m generator report-schema-audit
python -m generator report-schema-audit --format json --output reports/report-schema-audit.json
```

See [docs/REPORT_SCHEMA_CONTRACT.md](docs/REPORT_SCHEMA_CONTRACT.md).

### Report consistency audit

```bash
python -m generator report-consistency-audit
```

Validates that report status, defect details, and summary counts agree. See [Report Consistency Contract](docs/REPORT_CONSISTENCY_CONTRACT.md).


### Report provenance audit

Trace every tracked report to the CLI command that reproduces it:

```bash
python -m generator report-provenance-audit
python -m generator report-provenance-audit --format json --output reports/report-provenance-audit.json
```

See [docs/REPORT_PROVENANCE_CONTRACT.md](docs/REPORT_PROVENANCE_CONTRACT.md).

### Report determinism audit

Verify that registered audit reports render identically from an unchanged repository state:

```bash
python -m generator report-determinism-audit
```

See [Report Determinism Contract](docs/REPORT_DETERMINISM_CONTRACT.md).

### CLI output contract

```bash
python -m generator cli-output-audit
```

Validates JSON output, successful exit codes, and parity between stdout and `--output` for every registered report command.


### CLI exit-code contract

```bash
python -m generator cli-exit-code-audit
```

Verifies that passing audit JSON returns exit code `0` and failing audit JSON returns a non-zero process status. See [CLI Exit-Code Contract](docs/CLI_EXIT_CODE_CONTRACT.md).

### Report write-safety contract

```bash
python -m generator report-write-safety-audit
```

Verifies that audit output files are replaced atomically, failed writes preserve the previous report, and temporary files are cleaned up. See [Report Write-Safety Contract](docs/REPORT_WRITE_SAFETY_CONTRACT.md).

### Report refresh order audit

Validate that checked-in audit reports have a unique dependency-safe regeneration order and that archive-derived reports are rendered last:

```bash
python -m generator report-refresh-order-audit
```


### Report refresh command

Regenerate every tracked report in dependency-safe order with one command:

```bash
python -m generator report-refresh
python -m generator report-refresh --format json
```

Validate the command contract with `python -m generator report-refresh-audit`. See [Report Refresh Contract](docs/REPORT_REFRESH_CONTRACT.md).


### Audit performance contract

Validate timing instrumentation, one-execution-per-audit coverage, and the configurable instrumentation budget:

```bash
python -m generator audit-performance-audit
python -m generator audit-performance-audit --format json --output reports/audit-performance-audit.json
```

See [Audit Performance Contract](docs/AUDIT_PERFORMANCE_CONTRACT.md).

### Mod compatibility matrix

Validate the supported Minecraft/NeoForge platform and ensure every authored mod chapter is represented in the compatibility policy:

```bash
python -m generator mod-compatibility-audit
python -m generator mod-compatibility-audit --format json --output reports/mod-compatibility-audit.json
```

See [Mod Compatibility Matrix](docs/MOD_COMPATIBILITY.md). Exact mod build pins remain pack-managed; this repository validates integration coverage and compatibility status.

### Audit dependency contract

```bash
python -m generator audit-dependency-audit
python -m generator audit-dependency-audit --format json --output reports/audit-dependency-audit.json
```

Validates registered audit dependencies, rejects cycles and unknown prerequisites, and confirms quality-gate and report-refresh ordering is dependency-safe.

## Report refresh convergence

`python -m generator report-refresh` now repeats dependency-safe regeneration until the complete report set reaches a fixed point. Validate this behavior with `python -m generator report-refresh-convergence-audit`. See [Report Refresh Convergence Contract](docs/REPORT_REFRESH_CONVERGENCE_CONTRACT.md).

### Report refresh idempotence

Verify that an already-converged report refresh completes in one pass without rewriting files:

```bash
python -m generator report-refresh-idempotence-audit
```


### Release report finalization

Validate that archive-derived release reports remain the final, stable stage of report regeneration:

```bash
python -m generator release-report-finalization-audit
python -m generator release-package-verification-audit
```

### Release package verification

Run `python -m generator release-package-verification-audit` to independently verify the final ZIP inventory, checksums, reproducibility, and excluded-cache rules.


## Release manifest audit

Generate and verify a per-file manifest for the deterministic release package:

```bash
python -m generator release-manifest-audit
python -m generator release-manifest-audit --format json --output reports/release-manifest-audit.json
python -m generator release-archive-metadata-audit
python -m generator release-archive-metadata-audit --format json --output reports/release-archive-metadata-audit.json
```

### Release archive extraction safety

```bash
python -m generator release-archive-extraction-safety-audit
python -m generator release-archive-extraction-safety-audit --format json --output reports/release-archive-extraction-safety-audit.json
python -m generator release-archive-unicode-path-audit
python -m generator release-archive-unicode-path-audit --format json --output reports/release-archive-unicode-path-audit.json
python -m generator release-archive-compression-audit
python -m generator release-archive-compression-audit --format json --output reports/release-archive-compression-audit.json
```

Validates extraction-safe paths, normalized and case-folded uniqueness, and rejects links or special files.

## Autosave, snapshots, and crash recovery

The local editor automatically writes the current unsaved document after every accepted edit, bulk operation, layout change, undo, redo, generation, or import. Recovery files remain confined to the editor workspace and use atomic replacement so an interrupted write never exposes a partial JSON document.

Use **Snapshot** in the browser to create a named revision checkpoint and **Recover latest** to restore the current autosave. Saving the project clears the active autosave while preserving manual snapshots. Snapshot history is bounded to avoid unlimited workspace growth.

The recovery API is available at:

```text
GET  /api/v1/recovery
POST /api/v1/snapshot
POST /api/v1/recover
POST /api/v1/discard-recovery
```

Validate recovery behavior with:

```bash
python -m generator editor-recovery-audit
python -m generator editor-recovery-audit --format json --output reports/editor-recovery-audit.json
```

See [`docs/EDITOR_RECOVERY.md`](docs/EDITOR_RECOVERY.md).

## Background generation jobs and progress

Large modpack imports now run as staged localhost jobs instead of blocking one long browser request. The editor reports pack scanning, content discovery, progression planning, descriptions, rewards, and final graph validation with a monotonic progress bar and cooperative cancellation. The current document is replaced only after the generated graph validates successfully.

The job API is available at:

```text
GET  /api/v1/jobs
GET  /api/v1/jobs/{job-id}
POST /api/v1/jobs/{job-id}/cancel
POST /api/v1/generate-job
POST /api/v1/import-job
```

Validate background generation with:

```bash
python -m generator editor-jobs-audit
python -m generator editor-jobs-audit --format json --output reports/editor-jobs-audit.json
```

See [`docs/EDITOR_BACKGROUND_JOBS.md`](docs/EDITOR_BACKGROUND_JOBS.md).


## Portable project bundles and one-click installation

Save the generated editor project, source fingerprint, generation settings, and validated FTB Quests export in one shareable file:

```bash
python -m generator quest-project-bundle /path/to/modpack.mrpack \
  --destination shared.ftbqproj \
  --target-quests 600 \
  --reward-policy conservative
python -m generator quest-project-inspect shared.ftbqproj
python -m generator quest-project-install shared.ftbqproj /path/to/minecraft-instance
```

The installer verifies bundle checksums and SNBT, checks detected Minecraft/loader compatibility, installs atomically into `config/ftbquests`, and preserves the previous questbook in `.quest-maker-backups/`. The browser editor can reopen a shared `.ftbqproj` through its drop zone and exposes matching bundle and install controls.

Validate this workflow with:

```bash
python -m generator project-bundle-audit
python -m generator project-bundle-audit --format json --output reports/project-bundle-audit.json
```

See [`docs/PROJECT_BUNDLES_AND_INSTALLATION.md`](docs/PROJECT_BUNDLES_AND_INSTALLATION.md).
