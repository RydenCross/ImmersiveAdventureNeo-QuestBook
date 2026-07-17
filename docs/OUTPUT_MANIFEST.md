# Generated Output Manifest Guard

The output manifest records every generated FTB Quests file, its byte size, and SHA-256 digest. This catches stale checked-in outputs and reviewed build changes that a simple file-count check would miss.

Run the guard:

```bash
python -m generator output-manifest-guard
python -m generator output-manifest-guard --format json --output reports/output-manifest-guard.json
```

After an intentional generated-output change, refresh the manifest only after the determinism audit passes:

```bash
python -m generator output-manifest reports/generated-output-manifest.json
```

The guard fails for missing, unexpected, or byte-changed generated files.
