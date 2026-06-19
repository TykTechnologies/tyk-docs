"""AI-powered changelog entry enhancement using Claude API."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from release_notes_generator.config import ANTHROPIC_BASE_URL
from release_notes_generator.models import ChangelogEntry, Ticket

logger = logging.getLogger(__name__)

# Real examples extracted from tyk-docs gateway.mdx release notes.
# These show the exact style, structure, and tone used in production.
EXAMPLE_ENTRIES = """
Example 1 — Bug fix (explains broken -> impact -> fixed):

SUMMARY: Fixed Gateway Panic if HashiCorp Vault Path Not Found
DETAIL: Resolved an issue where the Gateway could crash with a panic if the API definition contained an illegal reference to a secret in HashiCorp Vault. If the requested path did not exist in Vault, this could cause the Gateway process to exit, resulting in a complete service outage during API loads, hot reloads, or Dashboard saves. The Gateway now gracefully handles the missing Vault path and logs a clear error message.

Example 2 — Bug fix (multi-paragraph with technical detail):

SUMMARY: Fixed Certificate Re-use After Swapping in Multi-Auth Keys
DETAIL: Resolved an issue where swapping certificates in multi-auth (mTLS + Basic auth) keys prevented the original certificate from being reused. Previously, when updating a key's certificate, the original certificate remained incorrectly associated with the key internally, causing "key with given certificate already found" errors when attempting to reuse that certificate.

Tyk now properly detaches certificates during key updates, allowing certificates to be freely reused across different keys after being removed from their original association.

Example 3 — Feature with config details and bullet list:

SUMMARY: Added Client Certificate-Token Binding for Auth Token APIs
DETAIL: This release introduces the ability to bind client certificates to Auth Tokens for APIs secured with a static mTLS allow list. This provides enhanced token security by ensuring tokens are only used with their associated certificates:

- Added a new `mtls_static_certificate_bindings` field to the session object, which accepts a list of one or more certificate IDs.
- Enforces that the certificate presented in the request matches the bound certificate IDs; otherwise, the request is rejected.
- Supports binding multiple client certificates to a single key (token) to facilitate certificate rotation.

This feature maintains full backward compatibility with existing keys that do not specify certificate bindings.

Example 4 — Feature with new config option:

SUMMARY: Configurable Gateway-Default JWKS Cache Timeout
DETAIL: The Gateway default JWKS cache validity period is now configurable via a new option in the Gateway config file: `jwks.cache.timeout` or the equivalent environment variable. If not set, the timeout continues to default to 240 seconds. This simplifies JWKS cache management across large API deployments while providing flexibility for APIs that require specific caching behaviors.

Example 5 — Changed/Updated (dependency bump, keep short):

SUMMARY: Updated Gateway to Go 1.25
DETAIL: Updated the Tyk Gateway to use Go 1.25, ensuring compatibility with the latest Go runtime features and reducing exposure to potential security vulnerabilities in older versions.

Example 6 — Security fix:

SUMMARY: Security Vulnerabilities Fixed
DETAIL: Addressed CVEs reported in dependent libraries, providing increased protection against security vulnerabilities.
""".strip()

SYSTEM_PROMPT = f"""You are a technical writer for Tyk Technologies. You write changelog entries for the tyk-docs release notes.

Your job: transform Jira ticket data into a polished, user-facing changelog entry.

## Writing Style (from real Tyk release notes)

**Voice & Tone:**
- Professional, technically precise, third person
- Use "we" for Tyk actions ("We've introduced..."), "you/users" for customer actions ("You can now...")
- Start titles with past-tense action verbs: "Added", "Fixed", "Resolved", "Improved", "Optimized", "Updated", "Restructured"
- No marketing language. No exclamation marks. No "we are excited/delighted".

**Bug Fixes — always follow this structure:**
1. State what was broken ("Resolved an issue where...")
2. Explain the user impact ("Previously, ... causing...")
3. State what's fixed now ("The Gateway now...", "Tyk now properly...")

**Features — include these when relevant:**
- What was added and why it matters to users
- New configuration options with their names in backticks (e.g., `enable_config_inspection`)
- Bullet lists for multi-point features (use markdown `-` bullets)
- Default values and backward compatibility ("disabled by default", "maintains full backward compatibility")

**Changed/Updated entries:**
- Keep short (1-2 sentences)
- Focus on what changed and why

**Formatting rules:**
- Use backticks for: config fields, environment variables, HTTP status codes (`HTTP 504`), API endpoints, header names
- Multi-paragraph entries: use actual newlines between paragraphs
- Bullet lists: use `- ` prefix per item
- Do NOT include the Jira ticket key (e.g., TT-12345) in the text
- Do NOT wrap output in markdown fences

## Examples

{EXAMPLE_ENTRIES}

## Output Format

Return EXACTLY this format. DETAIL can be multi-line:
SUMMARY: <title in past tense, 3-12 words>
DETAIL: <body text, can be multiple paragraphs, can include bullet lists>
"""


class AIEnhancer:
    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514", base_url: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("TYK_JIRA_API_TOKEN", "")
        if not self.api_key:
            raise ValueError("Set ANTHROPIC_API_KEY or TYK_JIRA_API_TOKEN.")
        self.base_url = base_url or ANTHROPIC_BASE_URL
        self.client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
        self.model = model

    def enhance_ticket(self, ticket: Ticket, category: str) -> ChangelogEntry:
        try:
            summary_line, detail_text = self._call_api(ticket, category)
        except Exception:
            logger.exception("AI enhancement failed for %s, using fallback", ticket.key)
            summary_line, detail_text = ticket.summary, ticket.best_text
        return ChangelogEntry(ticket_key=ticket.key, category=category, summary_line=summary_line,
                              detail_text=detail_text, is_breaking=ticket.is_breaking, breaking_description=ticket.breaking_change)

    def enhance_tickets(self, tickets: list[tuple[Ticket, str]], max_workers: int = 5) -> list[ChangelogEntry]:
        results: dict[int, ChangelogEntry] = {}
        def _enhance(i, ticket, category):
            logger.info("Enhancing ticket %d/%d: %s", i + 1, len(tickets), ticket.key)
            return i, self.enhance_ticket(ticket, category)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_enhance, i, t, c): i for i, (t, c) in enumerate(tickets)}
            for future in as_completed(futures):
                idx, entry = future.result()
                results[idx] = entry
        return [results[i] for i in range(len(tickets))]

    def generate_release_highlights(self, entries: list[ChangelogEntry]) -> str:
        summaries = "\n".join(f"- [{e.category}] {e.summary_line}" for e in entries)
        try:
            msg = self.client.messages.create(
                model=self.model, max_tokens=500,
                system=(
                    "You are a technical writer for Tyk Technologies. "
                    "Write a Release Highlights section for the release notes. "
                    "Use bold subsection headers like **Feature Name** followed by 1-2 paragraphs when there are significant features. "
                    "For patch releases with mostly bug fixes, write 2-3 concise sentences instead. "
                    "Focus on user impact. Be concise and professional. "
                    "Do not start with 'This release'. "
                    "End with: 'For a comprehensive list of changes, please refer to the detailed [changelog](#Changelog-vVERSION) below.' "
                    "(replace VERSION with the actual version)."
                ),
                messages=[{"role": "user", "content": f"Changelog entries:\n{summaries}"}])
            return msg.content[0].text.strip()
        except Exception:
            logger.exception("Failed to generate release highlights")
            return 'This release focuses mainly on bug fixes. For a comprehensive list of changes, please refer to the detailed [changelog](#Changelog-vVERSION) below.'

    def _call_api(self, ticket: Ticket, category: str) -> tuple[str, str]:
        parts = [
            f"Jira ticket: {ticket.key}",
            f"Issue type: {ticket.issue_type}",
            f"Category: {category}",
            f"Summary: {ticket.summary}",
        ]
        if ticket.has_release_notes:
            parts.append(f"Release Notes field: {ticket.release_notes_text}")
        if ticket.description:
            parts.append(f"Description: {ticket.description[:2000]}")
        if ticket.is_breaking:
            parts.append(f"Breaking Change: {ticket.breaking_change}")
        msg = self.client.messages.create(
            model=self.model, max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": "\n".join(parts)}],
        )
        text = msg.content[0].text.strip()
        return self._parse_response(text, ticket)

    @staticmethod
    def _parse_response(text: str, ticket: Ticket) -> tuple[str, str]:
        """Parse the SUMMARY/DETAIL response format.

        DETAIL can be multi-line — everything after the DETAIL: prefix
        until the end of the response.
        """
        summary_line = ""
        detail_lines: list[str] = []
        in_detail = False

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.upper().startswith("SUMMARY:"):
                summary_line = stripped[8:].strip()
                in_detail = False
            elif stripped.upper().startswith("DETAIL:"):
                detail_lines.append(stripped[7:].strip())
                in_detail = True
            elif in_detail:
                detail_lines.append(line.rstrip())

        detail_text = "\n".join(detail_lines).strip()

        return summary_line or ticket.summary, detail_text or ticket.best_text
