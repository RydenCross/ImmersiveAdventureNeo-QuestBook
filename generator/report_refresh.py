from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Mapping, Sequence

from generator.output_writer import atomic_write_text
from generator.report_refresh_cache import (
    DEFAULT_CACHE_FILENAME,
    default_fingerprints,
    file_digest,
    load_cache,
    write_cache,
)

DEFAULT_REPORT_DIRECTORY = Path("reports")
DEFAULT_MAX_PASSES = 4


@dataclass(frozen=True, slots=True)
class ReportRefresh:
    requested_reports: int
    refreshed_reports: tuple[str, ...]
    failed_reports: tuple[str, ...]
    passes: int
    converged: bool
    changed_reports_last_pass: tuple[str, ...]
    rendered_reports: tuple[str, ...] = ()
    skipped_reports: tuple[str, ...] = ()
    cache_used: bool = False
    cache_hits: int = 0
    cache_misses: int = 0
    cache_rebuilt: bool = False

    @property
    def is_clean(self) -> bool:
        return (
            self.converged
            and not self.failed_reports
            and len(self.refreshed_reports) == self.requested_reports
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "requested_reports": self.requested_reports,
            "refreshed_reports": list(self.refreshed_reports),
            "failed_reports": list(self.failed_reports),
            "passes": self.passes,
            "converged": self.converged,
            "changed_reports_last_pass": list(self.changed_reports_last_pass),
            "rendered_reports": list(self.rendered_reports),
            "skipped_reports": list(self.skipped_reports),
            "cache_used": self.cache_used,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_rebuilt": self.cache_rebuilt,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [
            f"Report refresh: {'PASS' if self.is_clean else 'FAIL'}",
            f"Requested reports: {self.requested_reports}.",
            f"Refreshed reports: {len(self.refreshed_reports)}.",
            f"Failed reports: {len(self.failed_reports)}.",
            f"Passes: {self.passes}.",
            f"Converged: {'yes' if self.converged else 'no'}.",
        ]
        if self.cache_used:
            lines.extend(
                (
                    f"Rendered reports: {len(self.rendered_reports)}.",
                    f"Skipped reports: {len(self.skipped_reports)}.",
                    f"Cache hits: {self.cache_hits}.",
                    f"Cache misses: {self.cache_misses}.",
                    f"Cache rebuilt: {'yes' if self.cache_rebuilt else 'no'}.",
                )
            )
        lines.extend(f"Failed: {name}" for name in self.failed_reports)
        lines.extend(f"Still changing: {name}" for name in self.changed_reports_last_pass)
        return "\n".join(lines)


def refresh_reports(
    report_directory: Path = DEFAULT_REPORT_DIRECTORY,
    *,
    renderers: Mapping[str, Callable[[], str]] | None = None,
    order: Sequence[str] | None = None,
    max_passes: int = DEFAULT_MAX_PASSES,
    incremental: bool = False,
    cache_path: Path | None = None,
    fingerprints: Mapping[str, Callable[[], str]] | None = None,
    root: Path = Path("."),
) -> ReportRefresh:
    if max_passes < 1:
        raise ValueError("max_passes must be at least 1")
    if renderers is None:
        from generator.report_freshness import _default_renderers

        renderers = _default_renderers()
    selected_order = tuple(order) if order is not None else tuple(renderers)
    report_directory.mkdir(parents=True, exist_ok=True)

    selected_cache_path = cache_path or (report_directory / DEFAULT_CACHE_FILENAME)
    cache_entries: dict[str, dict[str, str]] = {}
    cache_valid = False
    cache_rebuilt = False
    selected_fingerprints = fingerprints
    if incremental:
        cache_entries, cache_valid = load_cache(selected_cache_path, order=selected_order)
        cache_rebuilt = selected_cache_path.exists() and not cache_valid
        if selected_fingerprints is None:
            selected_fingerprints = default_fingerprints(
                selected_order,
                root=root,
                report_directory=report_directory,
                cache_path=selected_cache_path,
            )
        missing_fingerprints = tuple(name for name in selected_order if name not in selected_fingerprints)
        if missing_fingerprints:
            raise ValueError(
                "missing incremental fingerprints for: " + ", ".join(missing_fingerprints)
            )

    refreshed: list[str] = []
    failed: list[str] = []
    changed_last_pass: tuple[str, ...] = ()
    rendered_seen: list[str] = []
    skipped_seen: list[str] = []
    cache_hits = 0
    cache_misses = 0

    for pass_number in range(1, max_passes + 1):
        changed: list[str] = []
        failed_this_pass: list[str] = []
        for name in selected_order:
            renderer = renderers.get(name)
            if renderer is None:
                failed_this_pass.append(name)
                continue

            path = report_directory / name
            input_digest: str | None = None
            if incremental and selected_fingerprints is not None:
                try:
                    input_digest = str(selected_fingerprints[name]())
                except (OSError, TypeError, ValueError):
                    failed_this_pass.append(name)
                    continue
                existing_digest = file_digest(path)
                entry = cache_entries.get(name)
                if (
                    cache_valid
                    and entry is not None
                    and entry.get("input_digest") == input_digest
                    and existing_digest is not None
                    and entry.get("output_digest") == existing_digest
                ):
                    try:
                        json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, TypeError, ValueError, json.JSONDecodeError):
                        pass
                    else:
                        cache_hits += 1
                        if name not in skipped_seen:
                            skipped_seen.append(name)
                        if name not in refreshed:
                            refreshed.append(name)
                        continue
                cache_misses += 1

            try:
                rendered = renderer()
                json.loads(rendered)
                normalized = rendered.rstrip() + "\n"
                existing = path.read_text(encoding="utf-8") if path.is_file() else None
                if existing != normalized:
                    atomic_write_text(path, normalized)
                    changed.append(name)
                if incremental and input_digest is not None:
                    cache_entries[name] = {
                        "input_digest": input_digest,
                        "output_digest": file_digest(path) or "",
                    }
            except (OSError, TypeError, ValueError, json.JSONDecodeError):
                failed_this_pass.append(name)
                continue
            if name not in rendered_seen:
                rendered_seen.append(name)
            if name not in refreshed:
                refreshed.append(name)

        failed = failed_this_pass
        changed_last_pass = tuple(changed)
        if incremental:
            write_cache(selected_cache_path, order=selected_order, entries=cache_entries)
            cache_valid = True
        if failed:
            return ReportRefresh(
                requested_reports=len(selected_order),
                refreshed_reports=tuple(refreshed),
                failed_reports=tuple(failed),
                passes=pass_number,
                converged=False,
                changed_reports_last_pass=changed_last_pass,
                rendered_reports=tuple(rendered_seen),
                skipped_reports=tuple(skipped_seen),
                cache_used=incremental,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_rebuilt=cache_rebuilt,
            )
        if not changed:
            return ReportRefresh(
                requested_reports=len(selected_order),
                refreshed_reports=tuple(refreshed),
                failed_reports=(),
                passes=pass_number,
                converged=True,
                changed_reports_last_pass=(),
                rendered_reports=tuple(rendered_seen),
                skipped_reports=tuple(skipped_seen),
                cache_used=incremental,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_rebuilt=cache_rebuilt,
            )

    return ReportRefresh(
        requested_reports=len(selected_order),
        refreshed_reports=tuple(refreshed),
        failed_reports=tuple(failed),
        passes=max_passes,
        converged=False,
        changed_reports_last_pass=changed_last_pass,
        rendered_reports=tuple(rendered_seen),
        skipped_reports=tuple(skipped_seen),
        cache_used=incremental,
        cache_hits=cache_hits,
        cache_misses=cache_misses,
        cache_rebuilt=cache_rebuilt,
    )
