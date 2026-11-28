"""Data models for the release notes generator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Ticket:
    """A Jira ticket extracted from the API response."""

    key: str
    summary: str
    issue_type: str
    components: list[str] = field(default_factory=list)
    release_notes_text: str | None = None
    breaking_change: str | None = None
    description: str | None = None

    @property
    def has_release_notes(self) -> bool:
        return bool(self.release_notes_text and self.release_notes_text.strip())

    @property
    def is_breaking(self) -> bool:
        return bool(self.breaking_change and self.breaking_change.strip())

    @property
    def best_text(self) -> str:
        if self.has_release_notes:
            return self.release_notes_text.strip()
        return self.summary


@dataclass
class ChangelogEntry:
    ticket_key: str
    category: str
    summary_line: str
    detail_text: str
    is_breaking: bool = False
    breaking_description: str | None = None


@dataclass
class ReleaseSection:
    version: str
    release_date: str
    product: str
    product_label: str
    entries: list[ChangelogEntry] = field(default_factory=list)

    @property
    def major_minor(self) -> str:
        parts = self.version.split(".")
        return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else self.version

    @property
    def breaking_changes(self) -> list[ChangelogEntry]:
        return [e for e in self.entries if e.is_breaking]

    @property
    def added(self) -> list[ChangelogEntry]:
        return [e for e in self.entries if e.category == "Added"]

    @property
    def fixed(self) -> list[ChangelogEntry]:
        return [e for e in self.entries if e.category == "Fixed"]

    @property
    def changed(self) -> list[ChangelogEntry]:
        return [e for e in self.entries if e.category == "Changed"]

    @property
    def security_fixes(self) -> list[ChangelogEntry]:
        return [e for e in self.entries if e.category == "Security Fixes"]
