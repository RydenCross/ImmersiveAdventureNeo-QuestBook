# CLI Contract Audit

The CLI contract audit protects the repository's public command surface. It verifies that every expected subcommand is registered, each command has help text, and the installed `immersive-adventure-quests` entry point still targets `generator.cli:main`.

Run the audit:

```bash
python -m generator cli-audit
```

Write a machine-readable report:

```bash
python -m generator cli-audit --format json --output reports/cli-audit.json
```

The audit fails when a required command disappears, an unreviewed command is added, help text is missing, or the console-script target changes. Intentional command-surface changes must update `EXPECTED_COMMANDS` and the relevant documentation in the same commit.
