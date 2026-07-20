# Task Integrity Audit

The task integrity audit validates authored quest completion requirements independently of the broader release check.

```bash
python -m generator task-audit --strict
python -m generator task-audit --strict --format json --output reports/task-audit.json
```

The audit fails strict mode when it finds:

- task IDs reused by more than one quest;
- quests with no completion task;
- malformed item task resource locations or non-positive counts;
- malformed advancement IDs or non-string criteria;
- checkmark tasks carrying unexpected data; or
- empty custom task definitions.

The JSON report includes task totals grouped by type and lists every structural defect using the quest and task IDs needed to locate it.
