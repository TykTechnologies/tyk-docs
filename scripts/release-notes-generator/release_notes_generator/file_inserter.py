"""Insert generated release notes into existing tyk-docs markdown files."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from release_notes_generator.config import RELEASE_NOTES_DIR

logger = logging.getLogger(__name__)


def insert_release_section(file_path: Path, rendered_section: str, version: str) -> str:
    content = file_path.read_text(encoding="utf-8")
    major_minor = _extract_major_minor(version)
    if _is_new_minor_version(content, major_minor):
        return _insert_new_minor(content, rendered_section, major_minor)
    else:
        return _insert_patch(content, rendered_section, major_minor, version)


def _extract_major_minor(version: str) -> str:
    parts = version.split(".")
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else version


def _is_new_minor_version(content: str, major_minor: str) -> bool:
    return re.search(rf"^## {re.escape(major_minor)} Release Notes", content, re.MULTILINE) is None


def _insert_new_minor(content: str, rendered_section: str, major_minor: str) -> str:
    match = re.search(r"(## Support Lifetime.*?)(^---\s*$)", content, re.MULTILINE | re.DOTALL)
    if match:
        pos = match.end()
        return content[:pos] + "\n\n" + rendered_section + "\n\n---\n" + content[pos:]
    match = re.search(r"^## \d+\.\d+ Release Notes", content, re.MULTILINE)
    if match:
        return content[:match.start()] + rendered_section + "\n\n---\n\n" + content[match.start():]
    raise ValueError(f"Cannot find insertion point for {major_minor}.")


def _insert_patch(content: str, rendered_section: str, major_minor: str, version: str) -> str:
    header = re.search(rf"^## {re.escape(major_minor)} Release Notes\s*$", content, re.MULTILINE)
    if not header:
        raise ValueError(f"Cannot find '## {major_minor} Release Notes' section.")
    patch = re.search(rf"^### {re.escape(major_minor)}\.\d+ Release Notes", content[header.end():], re.MULTILINE)
    if patch:
        pos = header.end() + patch.start()
        return content[:pos] + rendered_section + "\n\n---\n\n" + content[pos:]
    return content[:header.end()] + "\n\n" + rendered_section + "\n" + content[header.end():]


def get_release_notes_path(repo_path: Path, release_notes_file: str) -> Path:
    return repo_path / RELEASE_NOTES_DIR / release_notes_file
