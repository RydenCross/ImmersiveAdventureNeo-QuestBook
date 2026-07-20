# Registry Audit

The registry audit checks every authored chapter icon, quest icon, item task, and item reward against item IDs discovered in mod JARs, ZIP archives, or JSON registry exports.

## Run against a mods directory

```bash
python -m generator registry-audit /path/to/instance/mods --strict
```

The directory scanner reads every `.jar`, `.zip`, and `.json` file directly inside the supplied directory. JAR scanning recognizes both Minecraft 1.21 item definition files under `assets/<namespace>/items/` and traditional item models under `assets/<namespace>/models/item/`.

## Run against a registry export

```bash
python -m generator registry-audit registry.json --strict
```

Supported JSON forms include a plain list of item IDs or an object such as:

```json
{
  "namespaces": ["minecraft", "create"],
  "items": [
    "minecraft:iron_ingot",
    "create:andesite_alloy"
  ]
}
```

`namespaces` is optional, but it is useful when a dump intentionally contains zero items for a namespace. Nested JSON values and registry objects keyed by item ID are also accepted.

## Result categories

- **Verified**: the exact item ID was found.
- **Missing**: the namespace was covered by the supplied sources, but the exact ID was not found.
- **Unverifiable**: no supplied source covered that namespace.

Only missing references make `--strict` fail. Unverifiable references are reported separately so partial mod sets can be audited without producing false failures.

## Limitations

Some mods register items dynamically without shipping a conventional item definition or model resource. For those mods, use a JSON registry export from the running instance for authoritative results. The audit does not alter quests automatically; it is a verification gate for deliberate content edits.

## Machine-readable reports

Use JSON output when integrating the audit into CI or external pack-maintenance tools:

```bash
python -m generator registry-audit /path/to/mods --format json
```

Write either text or JSON directly to a report file with `--output`:

```bash
python -m generator registry-audit /path/to/mods --format json --output reports/registry-audit.json
```

The JSON report includes summary counts, covered namespaces, source paths, and structured missing and unverifiable references.

## Reference manifest

Export every item ID authored by the questbook, grouped by namespace and usage type:

```bash
python -m generator registry-manifest --output reports/quest-item-manifest.json
```

This manifest is useful for comparing quest content against registry dumps, reviewing namespace coverage, or sharing the exact required item set with modpack maintainers.
