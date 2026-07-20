# Content Audit

The quest builder includes a source-level audit command:

```bash
python -m generator audit --strict
```

It reports:

- chapter and quest totals;
- optional quest count;
- task-type and reward-type coverage;
- empty quest descriptions;
- taskless quests;
- duplicate quest titles.

`--strict` returns a failing exit code when authored quests contain empty descriptions or no tasks. This complements the generated-project validator, which checks IDs, dependencies, cycles, coordinates, and resource-location syntax.
