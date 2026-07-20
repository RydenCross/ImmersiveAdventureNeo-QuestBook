from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Callable, Mapping

from generator.audit_registry_contract import AUDIT_REGISTRY

DEFAULT_BUDGET_MS = 250.0


@dataclass(frozen=True, slots=True)
class AuditTiming:
    name: str
    duration_ms: float

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "duration_ms": round(self.duration_ms, 3)}


@dataclass(frozen=True, slots=True)
class AuditPerformanceContract:
    registered_audits: int
    timed_audits: int
    total_duration_ms: float
    budget_ms: float
    duplicate_executions: tuple[str, ...]
    missing_timings: tuple[str, ...]
    over_budget: bool
    slowest_audits: tuple[AuditTiming, ...]

    @property
    def is_clean(self) -> bool:
        return not self.duplicate_executions and not self.missing_timings and not self.over_budget

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "registered_audits": self.registered_audits,
            "timed_audits": self.timed_audits,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "budget_ms": round(self.budget_ms, 3),
            "duplicate_executions": list(self.duplicate_executions),
            "missing_timings": list(self.missing_timings),
            "over_budget": self.over_budget,
            "slowest_audits": [item.to_dict() for item in self.slowest_audits],
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Audit performance contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Registered audits: {self.registered_audits}.",
                f"Timed audits: {self.timed_audits}.",
                f"Duplicate executions: {len(self.duplicate_executions)}.",
                f"Missing timings: {len(self.missing_timings)}.",
                f"Instrumentation duration: {self.total_duration_ms:.3f} ms / {self.budget_ms:.3f} ms budget.",
            )
        )


def run_audit_performance_contract(
    probes: Mapping[str, Callable[[], object]] | None = None,
    *,
    budget_ms: float = DEFAULT_BUDGET_MS,
    clock: Callable[[], float] | None = None,
) -> AuditPerformanceContract:
    names = tuple(item.gate_name for item in AUDIT_REGISTRY)
    selected = probes or {name: (lambda: None) for name in names}
    timer = clock or (lambda: 0.0)
    executions: list[str] = []
    timings: list[AuditTiming] = []
    for name, probe in selected.items():
        started = timer()
        probe()
        elapsed = max(0.0, (timer() - started) * 1000.0)
        executions.append(name)
        timings.append(AuditTiming(name=name, duration_ms=elapsed))

    duplicate_executions = tuple(
        sorted({name for name in executions if executions.count(name) > 1})
    )
    missing_timings = (
        tuple(sorted(set(names) - {item.name for item in timings})) if probes is None else ()
    )
    total = sum(item.duration_ms for item in timings)
    slowest = tuple(sorted(timings, key=lambda item: (-item.duration_ms, item.name))[:5])
    return AuditPerformanceContract(
        registered_audits=len(names),
        timed_audits=len(timings),
        total_duration_ms=total,
        budget_ms=budget_ms,
        duplicate_executions=duplicate_executions,
        missing_timings=missing_timings,
        over_budget=total > budget_ms,
        slowest_audits=slowest,
    )
