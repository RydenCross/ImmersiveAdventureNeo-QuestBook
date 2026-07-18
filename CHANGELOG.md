## Unreleased


## Commit 100 - Autosave, Project Snapshots, and Crash Recovery

- Added atomic editor autosave after every accepted document mutation.
- Added bounded, content-addressed project snapshots with checksum validation.
- Added recovery, snapshot, and discard endpoints to the local editor API.
- Added browser controls for manual snapshots and latest-autosave recovery.
- Added corruption, workspace-confinement, and save-clears-autosave coverage.

## Commit 99 - Graph Auto-Layout and Bulk Editing Workspace

- Added deterministic topological graph auto-layout with chapter scoping, stable coordinates, and collision prevention.
- Added atomic bulk quest operations with rollback-on-error and single-step undo/redo history.
- Added multi-selection controls for review flags and chapter movement in the browser editor.
- Added `/api/v1/auto-layout` and `/api/v1/batch-operations`, regression tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 98 - Drag-and-Drop Modpack Import and Interactive Quest Graph Canvas

- Added streamed browser import for CurseForge ZIPs, Modrinth `.mrpack` files, Prism exports, and server-pack archives.
- Added content-addressed, size-limited workspace storage with filename/path validation and no mod-code execution.
- Replaced the basic quest list with an interactive SVG dependency graph supporting node dragging, zoom, pan, search, chapter filtering, selection, and prerequisite linking.
- Added HTTP and direct-import regression tests, UI contract documentation, quality-gate integration, and a tracked audit report.

## Commit 97 - Local Visual Editor Service and API

- Added a dependency-free localhost browser editor backed by the versioned editor data model.
- Added versioned JSON endpoints for status, document access, validation, graph operations, undo/redo, save/open, regeneration, and FTB Quests export.
- Added workspace-confined file handling, loopback-only binding, bounded request bodies, and deterministic session behavior.
- Added CLI, contract tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 96 - Visual Questbook Editor Data Model

- Added a versioned deterministic JSON graph for chapters, quests, objectives, rewards, positions, and prerequisite edges.
- Added immutable editor operations with revision tracking, dirty-entity tracking, reversible transactions, and graph validation.
- Added blueprint round-trip and FTB Quests exporter compatibility for future desktop and web editor interfaces.
- Added public CLI generation, contract tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 95 - Quest Description and Instruction Generator

- Added deterministic concise, guided, and detailed description generation for scanned quest blueprints.
- Added prerequisite, recipe-input, tagged-input, chapter-entry, and downstream unlock guidance.
- Added explicit human-review instructions for low-confidence registry-only objectives.
- Applied guided descriptions to reward planning, FTB export, and generated questbook review by default.
- Added CLI, contract, documentation, and regression coverage.


## Commit 94 - Generated Quest Reward Planner

- Added deterministic `none`, `conservative`, `balanced`, and `generous` reward-decision policies.
- Added explicit no-reward decisions so the review stage can distinguish intentional omissions from unfinished work.
- Protected low-confidence quests from automatic rewards and used a portable vanilla utility reward palette.
- Added FTB item-reward export, CLI integration, contract tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 93 - Generated Questbook Review and Validation Report

- Added a public review command for generated modpack questbooks before publishing.
- Added structural checks for dependencies, cycles, objectives, duplicate goals, and export conversion.
- Added editorial findings for low-confidence quests, weak descriptions, reward decisions, oversized chapters, target shortfalls, and progression bottlenecks.
- Added deterministic JSON output, contract tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 92 - FTB Quests SNBT Blueprint Exporter

- Added deterministic conversion from generated quest blueprints into installable FTB Quests v13 SNBT directory trees.
- Added stable FTB IDs, item and advancement task conversion, cross-chapter dependency preservation, localized text, stale-file cleanup, parser round-trip validation, and tree checksums.
- Added public export CLI, exporter contract, regression tests, documentation, quality-gate integration, and a tracked audit report.

## Commit 91 - Progression Planner and Quest Blueprint Generator

- Added deterministic selection of scanned quest candidates with prerequisite closure and broad per-mod coverage.
- Added ordered, category-aware mod chapters, chapter splitting, cross-chapter prerequisites, and stable quest layout coordinates.
- Added configurable quest targets and chapter sizes, shortfall reporting, review-required flags, public CLI output, regression tests, documentation, quality-gate integration, and a tracked planner audit.

## Commit 90 - Recipe, Advancement, and Registry Scanner

- Added safe extraction of recipes, advancements, item registries, tags, and English item names from modpack JARs and bundled datapacks.
- Added deterministic quest candidates with objectives, source provenance, confidence scores, mod-balanced selection, and acyclic prerequisite edges.
- Added candidate-budget controls, malformed-JSON isolation, public CLI commands, documentation, regression fixtures, quality-gate integration, and a tracked scanner audit report.

## Commit 89 - Modpack Scanner and Pack Profile Generator

- Added safe offline scanning for Modrinth, CurseForge, Prism, server-pack, instance, and plain mods-directory inputs.
- Added NeoForge/Forge, Fabric, Quilt, legacy metadata, and manifest-only JAR inspection without executing mod code.
- Added normalized pack profiles with platform detection, mod classification, unresolved-reference reporting, quest weights, and recommended quest ranges.
- Added public CLI, deterministic scanner contract, regression fixtures, documentation, quality-gate integration, and a tracked audit report.

## Commit 88 - Incremental Report Refresh Cache

- Added an opt-in content-addressed cache for dependency-safe report regeneration.
- Added selective renderer invalidation, output-tamper detection, corrupt-cache recovery, and atomic cache writes.
- Added CLI flags, a dedicated cache contract, regression tests, documentation, quality-gate integration, and a tracked report.

- Added a 30-quest optional Challenges chapter covering megaprojects, stockpiles, automation, power reliability, magic, bosses, exploration, and completionist goals.

- Added a 24-quest Endgame chapter unifying automation, magic, equipment, storage, logistics, nuclear power, and final mastery objectives.

- Added 20 Mekanism Power and Reactors quests covering renewable generation, induction storage, fission safety, waste handling, turbines, and nuclear power mastery.
- Added 19 Create Automation quests covering belts, funnels, chutes, brass logistics, deployers, mechanical crafting, sequenced assembly, precision mechanisms, arms, and vaults.
- Added a 30-quest Mining chapter.
- Added cross-chapter progression from Survival into Mining.
- Added enchanting, diamond, ore-processing, and Nether-preparation progression.

## Commit 87 - Mod Compatibility Matrix

- Added a checked-in Minecraft 1.21.1 / NeoForge 21.1.x compatibility policy.
- Added matrix validation for all authored mod content modules, unique IDs, support states, and incompatibility declarations.
- Added CLI, report, documentation, quality-gate, and regression-test integration.
- Add release archive Unicode path contract for normalization, confusable, control-character, bidi, and portability checks.

## Commit 86 - Release Archive Compression Contract

- Added deterministic release ZIP compression-method, size-budget, and compression-savings validation.
- Integrated the contract into the quality gate, audit registry, dependency graph, CLI, freshness workflow, documentation, and test inventory.

## Commit 82 - Release Manifest Contract
- Added a release archive extraction safety contract for traversal, collision, symlink, and special-file defenses.

- Added a release archive metadata contract that canonicalizes and verifies ZIP timestamps, permissions, compression, path safety, encryption flags, and entry ordering.
- Added a deterministic per-file release manifest with path, byte size, and SHA-256.
- Added independent ZIP-to-manifest verification for missing, unexpected, resized, or changed entries.
- Excluded the generated manifest status report from its own release payload.

## Commit 80 - Release Report Finalization Contract

- Added `release-report-finalization-audit` and its tracked JSON report.
- Enforced final placement and follow-up stability for archive-derived release reports.

- Added a release package verification contract that cross-checks final ZIP inventory, archive and tree checksums, reproducibility, and hygiene exclusions.

## Commit 79 — Report Refresh Idempotence Contract

- Added `report-refresh-idempotence-audit` and its tracked JSON report.
- Proves that a converged report refresh completes in one pass without changing report contents or modification times.
- Integrated the contract into the quality gate, audit registry, dependency graph, CLI contracts, documentation, freshness checks, and test inventory.

## Commit 78 - Report Refresh Convergence Contract

- Made one report-refresh invocation iterate until no tracked report changes.
- Added configurable non-convergence protection and pass diagnostics.
- Added CLI, quality-gate, registry, freshness, dependency, documentation, and regression coverage.

## Commit 76 - Audit Performance Contract

- Added timing instrumentation and configurable budget validation for the registered audit inventory.
- Detects missing timings and duplicate audit executions without recursively rerunning the full quality gate.
- Integrated the contract into the CLI, quality gate, registry, freshness guard, tests, and documentation.

## Commit 75 - Report Refresh Command and Contract

- Added one-command dependency-safe regeneration for all tracked reports.
- Added atomic JSON validation and a companion report refresh contract.
- Integrated the contract into the CLI, quality gate, registry, freshness guard, tests, and documentation.

## Commit 74 - Report Refresh Order Contract

- Added a dependency-safe report refresh order contract.
- Required archive-derived reports to render after all other checked-in reports.
- Added CLI, quality-gate, freshness, registry, test, and documentation coverage.

## Commit 73 - Report Write-Safety Contract

- Added atomic report-file writes through a shared output helper.
- Added failure-path checks that preserve existing reports and clean temporary files.
- Integrated the contract into the CLI, quality gate, registry, freshness guard, tests, and documentation.

## Commit 72 - CLI Exit-Code Contract

- Added pass/fail exit-code verification through the public CLI.
- Added synthetic failure coverage for non-zero process status.
- Integrated the contract into the quality gate, report registry, freshness guard, documentation, and tests.

## Commit 71 - CLI Output Contract

- Added a contract for audit-command JSON, exit codes, and output-file parity.
- Integrated it into the quality gate, registry, test inventory, freshness guard, and documentation.

## Commit 70 - Report Determinism Contract

- Added `report-determinism-audit` to compare repeated JSON report renders.
- Registered the contract with the CLI, quality gate, freshness guard, test inventory, and audit registry.
- Added regression tests and machine-readable report output.

## Commit 69 - Report Provenance Contract

- Added `report-provenance-audit`.
- Added a machine-readable mapping from each tracked report to its registered generator command.
- Enforced command, renderer, registry, test, documentation, and quality-gate synchronization.

## Commit 68 - Report Consistency Contract

- Added `report-consistency-audit`.
- Enforced internal agreement between report status, defect lists, and summary counts.
- Integrated the contract into the quality gate, audit registry, freshness guard, CLI, tests, and documentation.

## Commit 67 - Report Schema Contract

- Added `report-schema-audit` to enforce a common machine-readable structure across registered audit reports.
- Detects missing reports, malformed JSON, non-object payloads, absent status fields, and invalid status values.
- Integrated the contract into the CLI, audit registry, test inventory, report freshness guard, documentation, and unified quality gate.

## Commit #66 — Test Inventory Contract

- Added a contract ensuring every registered quality-gate safeguard has a dedicated pytest module.
- Integrated test coverage inventory into the CLI, report freshness guard, documentation, and unified quality gate.

## Commit 65 - Audit Registry Contract

- Added `audit-registry-audit` to detect partially integrated or duplicate release safeguards.
- Registered the new audit in the CLI, unified quality gate, report freshness guard, documentation, and checked-in reports.

## Commit #64 — Release Reproducibility Audit

- Added independent release archive comparison by entry name and SHA-256 content digest.
- Integrated reproducibility validation into the CLI, quality gate, report freshness guard, and documentation contracts.

## Commit #63 — Release Artifact Audit

- Added a release archive integrity audit with JSON validation, empty-file detection, generated-output coverage, and forbidden artifact checks.
- Integrated the audit into the unified quality gate and report freshness guard.

## Commit #62 — Repository Hygiene Audit

- Added `python -m generator repository-hygiene-audit`.
- Enforces `.gitignore` coverage for caches, builds, package metadata, environment files, and key material.
- Detects forbidden build artifacts, secret-like filenames, and oversized accidental files.
- Removed generated `*.egg-info` metadata from the source archive.
- Added JSON reporting, documentation, quality-gate integration, freshness checks, and regression tests.

## Commit #60 — CLI Contract Audit
- Added a documentation contract audit for command coverage and local Markdown links.

- Added `python -m generator cli-audit` to protect the documented command surface.
- Validates all expected subcommands, help text, and the installed console entry point.
- Added the CLI audit to the unified quality gate and report freshness guard.
- Added machine-readable reporting, documentation, and regression tests.

## Commit #59 — Packaging Configuration and Audit

- Fixed explicit setuptools package discovery for `content`, `generator`, and `model`.
- Added the `immersive-adventure-quests` console command.
- Added a packaging audit to the unified quality gate.

## Commit 58 - Unified Quality Gate

- Added `python -m generator quality-gate` to run every repository-safe safeguard.
- Added combined text and JSON summaries with per-check pass/fail status.
- Simplified CI to enforce the complete validation suite through one command.
- Added quality-gate documentation and regression tests.

## Commit #57 — Report Freshness Guard

- Added `report-freshness-guard` to compare checked-in JSON reports with current audit results.
- Detects stale, missing, and invalid derived reports.
- Added CI enforcement and machine-readable freshness reporting.

# Commit 56 - Generated Output Manifest Guard

- Added per-file SHA-256 and byte-size tracking for generated questbook output.
- Added safe manifest refresh gated by the build determinism audit.
- Added CI enforcement, JSON reporting, documentation, and regression tests.

# Commit 55 - Build Determinism Audit

- Added byte-for-byte comparison of two isolated questbook builds.
- Added generated-tree SHA-256 reporting and CI enforcement.
- Added regression tests and determinism documentation.

## Commit #54 — Quest Text Quality Audit

- Added strict placeholder, formatting, and duplicate-description validation.
- Added JSON reporting and CI integration.


## Commit 53 - Chapter Integrity Audit

- Added chapter UUID, FTB ID, title, icon, and description validation.
- Added ordered `NN_slug` ID and `order_index` consistency checks.
- Added strict detection for duplicate identities and empty chapters.
- Added CLI, CI report generation, documentation, and regression tests.

## Commit 52 - Task Integrity Audit

- Added global task ID uniqueness and task-data validation.
- Added item count/resource-location and advancement identifier checks.
- Added strict detection for taskless quests and malformed checkmark/custom tasks.
- Added CLI, CI report generation, documentation, and regression tests.

## Commit 51 - Reward Integrity Audit

- Added reward ID uniqueness and reward-data validation.
- Added item resource-location and positive-count checks.
- Added informational reporting for terminal quests without rewards.
- Added CLI, CI report generation, documentation, and regression tests.

## Commit 50 - Quest Contract Guard

- Added a checked-in quest contract baseline covering icons, difficulty, quest flags, task IDs/types, and reward IDs/types.
- Added `contract-guard` and `contract-baseline` commands.
- Allowed normal description edits and newly added quests without failing the guard.
- Added CI enforcement, documentation, JSON reporting, and regression tests.

## Commit 48 - Progression Complexity Guard

- Added `progression-guard` with checked-in progression complexity limits.
- Detects quest or dependency count reductions, critical-path growth, excessive bottlenecks, high direct fan-out, and unexpected cross-chapter coupling.
- Added JSON reporting, documentation, CI enforcement, and regression tests.

## Commit 47 - Progression Metrics and Bottleneck Analysis

- Added critical-path depth calculation for the authored dependency graph.
- Added bottleneck detection for quests with four or more direct dependants.
- Added cross-chapter transition metrics with text and JSON reports.
- Added CLI, documentation, CI report generation, and regression tests.

## Commit 46 - Progression Graph Export

- Added Graphviz DOT and JSON dependency graph exports.
- Grouped quest nodes by chapter and marked optional quests visually.
- Added CLI, documentation, generated reports, and automated tests.

## Commit 45 - Quest Dependency Analyzer

- Added progression graph analysis for cycles, reachability, duplicate dependencies, and chapter entry paths.
- Added text and JSON `dependency-audit` reports with strict CI behavior.
- Added dependency-audit tests, documentation, and CI integration.

## Commit 44 - Safe Baseline Refresh

- Added `release-baseline` for validated baseline updates.
- Refuses to overwrite the baseline when the release check fails.
- Creates missing report directories automatically.

## Commit 43 - Baseline Release Guard

- Added `release-guard` to compare a clean release check with a checked-in baseline.
- Added `reports/release-baseline.json`, JSON output, tests, documentation, and CI enforcement.

## Commit 42 - Release Report Comparison

- Added `python -m generator release-compare` for comparing machine-readable release reports.
- Added strict regression detection for content totals, validation, quality metrics, and authored/generated parity.
- Added text and JSON comparison reports, file output, documentation, and regression tests.

## Commit 41 - Machine-Readable Release Reports

- Added JSON output for `release-check`.
- Added `--report-output` for persistent text or JSON release reports.
- Added structured pass/fail and verification totals for CI and release tooling.
- Expanded release-check documentation and regression coverage.

## Commit 40 - Unified Release Check

- Added `python -m generator release-check`.
- Builds, reparses, and validates generated FTB Quests output.
- Combines graph validation, content-quality auditing, generated count parity, and registry-manifest checks.
- Added optional persistent output via `--output`.
- Updated CI to use the unified release gate.
- Added release-check documentation and regression tests.

## Commit 39 - Registry Reports and Reference Manifest

- Added machine-readable JSON output for `registry-audit`.
- Added `--output` support for text and JSON audit reports.
- Added `registry-manifest` for exporting every authored item reference by namespace and usage type.
- Added report and manifest regression tests.
- Expanded registry workflow documentation and README examples.

## Commit 38 - Mod Registry Verification

- Added `python -m generator registry-audit` for verifying authored item references.
- Added JAR/ZIP scanning for Minecraft 1.21 item definitions and traditional item models.
- Added flexible JSON registry-export support with explicit namespace coverage.
- Added verified, missing, and unverifiable result categories.
- Added strict CI-friendly failure behavior for covered but missing item IDs.
- Added registry audit documentation and regression tests.

## Commit 37 - Content Audit and Documentation Polish

- Added `python -m generator audit` for source-level questbook quality checks.
- Added strict audit regression tests.
- Replaced the outdated early-development README with current build, lint, audit, and questbook information.
- Documented the content-audit workflow.

## Commit 35 - AE2 Expansion

- Added 20 optional AE2 quests for bulk storage, advanced autocrafting, redundancy, spatial storage, and quantum networking.
- Added `content/ae2/quantum_engineering.py`.
- Preserved **Master of the ME Network** as the downstream chapter handoff.
- Added expansion documentation and regression coverage.

## Commit 34 - Apotheosis Expansion

- Added 20 optional Apotheosis quests for mythic hunting, gem refinement, specialized reforging, advanced enchanting, legendary loadouts, and mastery trials.
- Added `content/apotheosis/mythic_mastery.py`.
- Preserved **Apotheosis Mastery** as the downstream chapter handoff.
- Expanded the generated questbook beyond 600 quests.
- Added expansion documentation and regression coverage.

## Commit 33 - Ars Nouveau Expansion

- Added 20 optional Ars Nouveau quests for Source infrastructure, rituals, familiars, automated spellcasting, magical transport, and an archmage-scale workshop.
- Added `content/ars_nouveau/archmage_workshop.py`.
- Preserved **Master of Practical Spellcraft** as the downstream chapter handoff.
- Added expansion documentation and regression coverage.

## Commit 32 - Actually Additions Expansion

- Added 20 optional Actually Additions quests for advanced power, empowered crystals, laser-relay networks, and workshop automation.
- Added `content/actually_additions/advanced_workshop.py`.
- Preserved **Actually Equipped** as the downstream chapter handoff.
- Added expansion documentation and regression coverage.

## Commit 31 - Exploration Expansion

- Added 20 optional post-mastery Exploration quests.
- Added archaeology, Nether, monument, mansion, ancient-city, stronghold, and End-city expeditions.
- Preserved Experienced Explorer as the chapter completion returned to downstream content.
- Expanded regression coverage to 556 generated quests.

## Commit 30 - Survival Expansion

- Added 20 optional post-homestead Survival quests.
- Added crop diversity, fishing, beekeeping, and vanilla workshop branches.
- Preserved Mining and Exploration unlocks at A Proper Homestead.
- Expanded regression coverage to 536 generated quests.

## Commit 29 - Create Addons

- Added a 31-quest Create Addons chapter.
- Covered electrical, diesel, artillery, railway, contraption utility, and aviation expansions.
- Added regression coverage and addon documentation.

## Unreleased

## 0.1.0 - 2026-07-16

- Added the repository structure.
- Added the Immersive Adventure Neo Welcome chapter.
- Added eight linked quests and starter rewards.
- Added deterministic quest ID generation.
- Added FTB Quests v13 baseline configuration and localization.

## 0.1.0-alpha.2

- Added the generated Survival chapter with 25 quests.
- Added cross-chapter progression from Welcome into Survival.
- Expanded generated output to 2 chapters and 34 quests.
- Added Survival content and build regression tests.

## 0.1.0-alpha.1
- Idea
