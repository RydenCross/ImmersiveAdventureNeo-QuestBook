# Mod Compatibility Matrix

The checked-in policy at `config/mod-compatibility.json` is the source of truth for the questbook's supported platform and authored mod chapters.

Run:

```bash
python -m generator mod-compatibility-audit
python -m generator mod-compatibility-audit --format json --output reports/mod-compatibility-audit.json
```

The audit verifies that every authored `content/` module has exactly one declared mod, mod IDs and modules are unique, platform metadata is complete, status and requirement values are valid, and incompatibility pairs reference real distinct mods.

Version policy is deliberately `pack-managed`: exact mod build pins belong in the modpack lockfile, while this repository records the Minecraft/NeoForge line and the compatibility status of each quest integration.
