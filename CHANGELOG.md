# Changelog

## Commit 45 - Quest Dependency Analyzer

- Added progression graph analysis for cycles, reachability, duplicate dependencies, and chapter entry paths.
- Added text and JSON `dependency-audit` reports with strict CI behavior.
- Added dependency-audit tests, documentation, and CI integration.


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

## Commit 29 - Create Addons

- Added a 31-quest Create Addons chapter.
- Covered electrical, diesel, artillery, railway, contraption utility, and aviation expansions.
- Added regression coverage and addon documentation.

## Commit 37 - Content Audit and Documentation Polish

- Added `python -m generator audit` for source-level questbook quality checks.
- Added strict audit regression tests.
- Replaced the outdated early-development README with current build, lint, audit, and questbook information.
- Documented the content-audit workflow.
