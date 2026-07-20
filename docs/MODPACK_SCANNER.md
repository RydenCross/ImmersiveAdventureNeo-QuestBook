# Modpack Scanner and Pack Profile Generator

The modpack scanner is the first reusable engine component for the planned FTB Quest Maker app. It reads pack metadata and mod JAR resources without importing or executing mod classes.

## Supported inputs

```bash
python -m generator modpack-scan /path/to/modpack.mrpack
python -m generator modpack-scan /path/to/curseforge-export.zip
python -m generator modpack-scan /path/to/prism-instance
python -m generator modpack-scan /path/to/server-pack.zip
python -m generator modpack-scan /path/to/instance/mods
```

The scanner recognizes:

- Modrinth `.mrpack` archives and unpacked `modrinth.index.json` directories
- CurseForge exports containing `manifest.json`
- Prism Launcher instances using `mmc-pack.json`
- Server or instance ZIPs containing a `mods` directory
- Plain Minecraft instance directories
- Plain `mods` directories

## Machine-readable profile

```bash
python -m generator modpack-scan pack.mrpack \
  --format json \
  --output pack-profile.json
```

The generated profile contains:

- Pack name and version
- Minecraft version
- Mod loader and loader version
- Normalized mod IDs, display names, and versions when available
- Metadata source and source reference
- Resolved versus inferred mod identities
- Content-mod and library-mod classification
- Broad gameplay categories
- Per-mod quest weights
- Recommended minimum, target, and maximum quest counts
- Warnings and blocking scan errors

## Safe JAR inspection

The scanner treats JARs as ZIP archives and reads metadata only. It never imports classes, starts Minecraft, invokes mod entrypoints, or executes scripts from the pack.

Supported embedded metadata includes:

- `META-INF/neoforge.mods.toml`
- `META-INF/mods.toml`
- `fabric.mod.json`
- `quilt.mod.json`
- `mcmod.info`
- `META-INF/MANIFEST.MF` as a fallback

Archive entry and metadata-size limits reduce accidental resource exhaustion during inspection.

## Remote manifest limitations

CurseForge exports normally contain project and file IDs rather than downloaded mod JARs. Those entries are preserved as unresolved source references such as `curseforge:1234:5678`. Modrinth file paths can provide a useful inferred identity, but exact mod IDs still require embedded JAR metadata or a later metadata-resolution phase.

Unresolved entries do not make a scan fail. They are highlighted so a later app stage can resolve them through downloaded pack files, user-supplied instances, or optional platform APIs.

## Quest-count recommendation

The current recommendation is intentionally heuristic. Libraries receive zero quest weight, while gameplay mods receive weights based on broad categories and known large progression mods. The result is a planning target, not a generated questbook yet.

A later phase will replace these coarse weights with recipe counts, advancements, item registries, machine tiers, dimensions, bosses, and curated mod profiles.

## Scanner contract

```bash
python -m generator modpack-scanner-audit
python -m generator modpack-scanner-audit \
  --format json \
  --output reports/modpack-scanner-audit.json
```

The contract uses deterministic synthetic fixtures to verify:

- Modrinth detection
- CurseForge detection
- NeoForge JAR metadata extraction
- Minecraft and loader detection
- Quest-target generation
- Rejection of corrupt archives
