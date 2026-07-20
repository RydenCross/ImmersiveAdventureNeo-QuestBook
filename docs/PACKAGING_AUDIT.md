# Packaging Audit

The packaging audit verifies that the repository can be installed by standard Python tooling without setuptools treating the top-level packages as an ambiguous flat layout.

```bash
python -m generator packaging-audit
```

It checks explicit discovery for `content`, `generator`, and `model`, plus the installed `immersive-adventure-quests` console command.
