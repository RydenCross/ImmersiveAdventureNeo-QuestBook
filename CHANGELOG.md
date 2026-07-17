## Commit #66 — Test Inventory Contract

- Added a contract ensuring every registered quality-gate safeguard has a dedicated pytest module.
- Integrated test coverage inventory into the CLI, report freshness guard, documentation, and unified quality gate.

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

# Changelog

## Commit 58 - Unified Quality Gate

- Added `python -m generator quality-gate` to run every repository-safe safeguard.
- Added combined text and JSON summaries with per-check pass/fail status.
- Simplified CI to enforce the complete validation suite through one command.
- Added quality-gate documentation and regression tests.

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

# Changelog

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

## Unreleased

- Added 20 optional Mekanism endgame quests covering fusion, antimatter, grid-scale storage, MekaSuit equipment, radioactive logistics, and industrial mastery.

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

- Added a 30-quest optional Challenges chapter covering megaprojects, stockpiles, automation, power reliability, magic, bosses, exploration, and completionist goals.

- Added a 24-quest Endgame chapter unifying automation, magic, equipment, storage, logistics, nuclear power, and final mastery objectives.

- Added 20 Mekanism Power and Reactors quests covering renewable generation, induction storage, fission safety, waste handling, turbines, and nuclear power mastery.
- Added 19 Create Automation quests covering belts, funnels, chutes, brass logistics, deployers, mechanical crafting, sequenced assembly, precision mechanisms, arms, and vaults.
- Added a 30-quest Mining chapter.
- Added cross-chapter progression from Survival into Mining.
- Added enchanting, diamond, ore-processing, and Nether-preparation progression.

# Changelog

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
## Commit #57 — Report Freshness Guard

- Added `report-freshness-guard` to compare checked-in JSON reports with current audit results.
- Detects stale, missing, and invalid derived reports.
- Added CI enforcement and machine-readable freshness reporting.

## Commit 65 - Audit Registry Contract

- Added `audit-registry-audit` to detect partially integrated or duplicate release safeguards.
- Registered the new audit in the CLI, unified quality gate, report freshness guard, documentation, and checked-in reports.


## Commit 67 - Report Schema Contract

- Added `report-schema-audit` to enforce a common machine-readable structure across registered audit reports.
- Detects missing reports, malformed JSON, non-object payloads, absent status fields, and invalid status values.
- Integrated the contract into the CLI, audit registry, test inventory, report freshness guard, documentation, and unified quality gate.
