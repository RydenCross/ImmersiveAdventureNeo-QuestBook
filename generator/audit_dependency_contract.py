from __future__ import annotations

from dataclasses import dataclass
import json

from generator.audit_registry_contract import AUDIT_REGISTRY

# Dependencies are expressed by quality-gate names. Most content audits are roots;
# framework contracts depend on the registries or surfaces they validate.
AUDIT_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    item.gate_name: () for item in AUDIT_REGISTRY
}
AUDIT_DEPENDENCIES.update(
    {
        "output manifest guard": ("determinism audit",),
        "report freshness guard": ("output manifest guard",),
        "release artifact audit": ("repository hygiene audit", "packaging audit"),
        "release reproducibility audit": ("release artifact audit",),
        "audit registry contract": ("CLI contract audit",),
        "test inventory contract": ("audit registry contract",),
        "report schema contract": ("audit registry contract",),
        "report consistency contract": ("report schema contract",),
        "report provenance contract": ("audit registry contract",),
        "report determinism contract": ("report provenance contract",),
        "CLI output contract": ("CLI contract audit", "report schema contract"),
        "CLI exit-code contract": ("CLI output contract",),
        "report write-safety contract": ("CLI output contract",),
        "report refresh order contract": ("report provenance contract",),
        "report refresh contract": ("report refresh order contract", "report write-safety contract"),
        "report refresh convergence contract": ("report refresh contract",),
        "report refresh idempotence contract": ("report refresh convergence contract",),
        "report refresh cache contract": ("report refresh convergence contract", "report write-safety contract"),
        "release report finalization contract": ("report refresh idempotence contract", "report refresh order contract"),
        "release package verification contract": ("release report finalization contract",),
        "release manifest contract": ("release package verification contract",),
        "release archive metadata contract": ("release manifest contract",),
        "release archive extraction safety contract": ("release archive metadata contract",),
        "release archive Unicode path contract": ("release archive extraction safety contract",),
        "release archive compression contract": ("release archive metadata contract",),
        "modpack scanner contract": ("repository hygiene audit",),
        "modpack content scanner contract": ("modpack scanner contract",),
        "progression planner contract": ("modpack content scanner contract",),
        "FTB blueprint exporter contract": ("progression planner contract",),
        "audit performance contract": ("audit registry contract",),
        "audit dependency contract": ("audit registry contract", "report refresh order contract"),
    }
)


@dataclass(frozen=True, slots=True)
class AuditDependencyContract:
    registered_audits: int
    dependency_edges: int
    missing_nodes: tuple[str, ...]
    unknown_dependencies: tuple[str, ...]
    dependency_cycles: tuple[str, ...]
    gate_order_violations: tuple[str, ...]
    refresh_order_violations: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_nodes, self.unknown_dependencies, self.dependency_cycles,
                        self.gate_order_violations, self.refresh_order_violations))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "registered_audits": self.registered_audits,
            "dependency_edges": self.dependency_edges,
            "missing_nodes": list(self.missing_nodes),
            "unknown_dependencies": list(self.unknown_dependencies),
            "dependency_cycles": list(self.dependency_cycles),
            "gate_order_violations": list(self.gate_order_violations),
            "refresh_order_violations": list(self.refresh_order_violations),
            "dependencies": {name: list(deps) for name, deps in sorted(AUDIT_DEPENDENCIES.items())},
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join((
            f"Audit dependency contract: {'PASS' if self.is_clean else 'FAIL'}",
            f"Registered audits: {self.registered_audits}.",
            f"Dependency edges: {self.dependency_edges}.",
            f"Unknown dependencies: {len(self.unknown_dependencies)}.",
            f"Dependency cycles: {len(self.dependency_cycles)}.",
            f"Gate order violations: {len(self.gate_order_violations)}.",
            f"Refresh order violations: {len(self.refresh_order_violations)}.",
        ))


def _cycles(graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    visiting: set[str] = set()
    visited: set[str] = set()
    found: set[str] = set()
    def visit(node: str, path: tuple[str, ...]) -> None:
        if node in visiting:
            start = path.index(node)
            found.add(" -> ".join(path[start:] + (node,)))
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, ()):
            if dependency in graph:
                visit(dependency, path + (dependency,))
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node, (node,))
    return tuple(sorted(found))


def _order_violations(order: tuple[str, ...], graph: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    positions = {name: index for index, name in enumerate(order)}
    return tuple(sorted(
        f"{dependency} -> {name}"
        for name, dependencies in graph.items()
        for dependency in dependencies
        if name in positions and dependency in positions and positions[dependency] > positions[name]
    ))


def run_audit_dependency_contract(
    dependencies: dict[str, tuple[str, ...]] | None = None,
) -> AuditDependencyContract:
    from generator.quality_gate import _default_checks
    from generator.report_freshness import report_refresh_order

    graph = dependencies or AUDIT_DEPENDENCIES
    registered = tuple(item.gate_name for item in AUDIT_REGISTRY)
    registered_set = set(registered)
    missing_nodes = tuple(sorted(registered_set - set(graph)))
    unknown = tuple(sorted({dep for deps in graph.values() for dep in deps if dep not in registered_set}))
    gate_order = tuple(_default_checks())
    report_to_gate = {item.report: item.gate_name for item in AUDIT_REGISTRY if item.report}
    refresh_gate_order = tuple(report_to_gate[name] for name in report_refresh_order() if name in report_to_gate)
    return AuditDependencyContract(
        registered_audits=len(registered),
        dependency_edges=sum(len(value) for value in graph.values()),
        missing_nodes=missing_nodes,
        unknown_dependencies=unknown,
        dependency_cycles=_cycles(graph),
        gate_order_violations=_order_violations(gate_order, graph),
        refresh_order_violations=_order_violations(refresh_gate_order, graph),
    )
