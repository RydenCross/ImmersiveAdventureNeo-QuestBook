from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from generator.cli_audit import EXPECTED_COMMANDS

DEFAULT_README = Path("README.md")
DEFAULT_DOCS = Path("docs")
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

@dataclass(frozen=True, slots=True)
class DocumentationAudit:
    markdown_files: tuple[str, ...]
    missing_command_docs: tuple[str, ...]
    broken_links: tuple[str, ...]
    empty_documents: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        return not any((self.missing_command_docs, self.broken_links, self.empty_documents))

    def to_dict(self) -> dict[str, object]:
        return {"status": "pass" if self.is_clean else "fail", "markdown_file_count": len(self.markdown_files), "markdown_files": list(self.markdown_files), "documented_command_count": len(EXPECTED_COMMANDS) - len(self.missing_command_docs), "expected_command_count": len(EXPECTED_COMMANDS), "missing_command_docs": list(self.missing_command_docs), "broken_links": list(self.broken_links), "empty_documents": list(self.empty_documents)}

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        lines = [f"Documentation contract audit: {'PASS' if self.is_clean else 'FAIL'}", f"Markdown files: {len(self.markdown_files)}.", f"Documented commands: {len(EXPECTED_COMMANDS) - len(self.missing_command_docs)}/{len(EXPECTED_COMMANDS)}.", f"Broken links: {len(self.broken_links)}.", f"Empty documents: {len(self.empty_documents)}."]
        lines.extend(f"Missing command documentation: {name}" for name in self.missing_command_docs)
        lines.extend(f"Broken link: {item}" for item in self.broken_links)
        lines.extend(f"Empty document: {item}" for item in self.empty_documents)
        return "\n".join(lines)

def run_documentation_audit(readme: Path = DEFAULT_README, docs: Path = DEFAULT_DOCS) -> DocumentationAudit:
    files = tuple(path for path in (readme, *sorted(docs.rglob("*.md"))) if path.is_file())
    texts = {path: path.read_text(encoding="utf-8") for path in files}
    combined = "\n".join(texts.values())
    missing = tuple(sorted(command for command in EXPECTED_COMMANDS if f"python -m generator {command}" not in combined and f"immersive-adventure-quests {command}" not in combined))
    broken = []
    for source, text in texts.items():
        for target in _MARKDOWN_LINK.findall(text):
            clean = target.split("#", 1)[0].strip()
            if clean and "://" not in clean and not clean.startswith("mailto:") and not (source.parent / clean).resolve().exists():
                broken.append(f"{source.as_posix()} -> {target}")
    empty = tuple(sorted(path.as_posix() for path, text in texts.items() if not text.strip()))
    return DocumentationAudit(tuple(path.as_posix() for path in files), missing, tuple(sorted(set(broken))), empty)
