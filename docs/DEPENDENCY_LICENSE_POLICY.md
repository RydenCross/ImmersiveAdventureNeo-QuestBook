# Dependency License Inventory and Distribution Policy

Commit 115 adds a deterministic license policy for every package in `requirements-ci.lock`.

`dependency-licenses.json` records SPDX expressions, approved licenses, denied licenses, and narrowly reviewed exceptions. A dependency is blocked when its license is missing, denied, unknown, or outside the allow list without a documented exception.

Generate the distributable inventory:

```bash
python -m generator quest-maker-license-inventory --output dependency-license-inventory.json
```

Validate the repository policy:

```bash
python -m generator dependency-license-audit --format json
```

Exceptions must identify an existing locked package and contain a non-empty review reason. The generated inventory never modifies the policy source.
