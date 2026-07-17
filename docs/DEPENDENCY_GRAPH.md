# Dependency Graph Export

Export the authored quest progression graph for visual review or external analysis.

```bash
python -m generator dependency-graph --output reports/dependency-graph.dot
python -m generator dependency-graph --format json --output reports/dependency-graph.json
```

The DOT output groups quests into chapter clusters and renders optional quests with dashed borders. Render it with Graphviz, for example: `dot -Tsvg reports/dependency-graph.dot -o dependency-graph.svg`.

The JSON output includes chapter metadata, quest metadata, and every directed prerequisite edge.
