# Audit Dependency Contract

Run `python -m generator audit-dependency-audit` to validate the dependency graph for all registered quality safeguards.

The contract rejects missing graph nodes, references to unknown audits, dependency cycles, and execution or report-refresh orders that place an audit before one of its prerequisites. JSON output is available with `--format json --output reports/audit-dependency-audit.json`.
