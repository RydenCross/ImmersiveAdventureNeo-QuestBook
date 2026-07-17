# Release Check

Run the repository-safe release gate with:

```bash
python -m generator release-check
```

The command performs these checks in one deterministic pass:

1. Builds the authored project.
2. Writes generated FTB Quests SNBT to a temporary directory.
3. Reparses the generated files.
4. Validates authored and generated quest graphs.
5. Confirms authored and generated chapter/quest totals match.
6. Runs the content-quality audit.
7. Builds and parses the registry-reference manifest.

A non-zero exit code is returned for validation errors, warnings, empty descriptions, taskless quests, duplicate titles, or authored/generated count mismatches.

To keep the generated output for inspection:

```bash
python -m generator release-check --output release-output
```

Registry verification against actual mod IDs still requires the modpack JARs and remains a separate `registry-audit` step.
