# Dependency Audit

The dependency audit analyzes authored quest progression as a directed graph.

```bash
python -m generator dependency-audit --strict
```

It fails in strict mode when it finds dependency cycles, quests unreachable from every global
entry quest, duplicate prerequisite declarations, or a chapter with no quest that can be entered
from outside that chapter.

## JSON report

```bash
python -m generator dependency-audit --strict \
  --format json \
  --output reports/dependency-audit.json
```

The report also includes graph totals, entry quests, and terminal quests for release diagnostics.
