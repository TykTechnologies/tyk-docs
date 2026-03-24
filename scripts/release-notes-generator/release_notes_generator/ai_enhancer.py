"""AI-powered changelog entry enhancement using Claude API."""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from release_notes_generator.config import ANTHROPIC_BASE_URL
from release_notes_generator.models import ChangelogEntry, Ticket

logger = logging.getLogger(__name__)

EXAMPLE_ENTRIES = """
Example 1 (Bug fix):
<summary>Fixed Gateway panic and SSE streaming issue with OpenTelemetry</summary>

Resolved a bug that prevented upstream server-sent events (SSE) from being sent when OpenTelemetry was enabled, and fixed a gateway panic that occurred when detailed recording was active while SSE was in use. This ensures stable SSE streaming in configurations with OpenTelemetry.

Example 2 (Bug fix):
<summary>Request size limit middleware would block any request without a payload (for example GET, DELETE)</summary>

Resolved a problem in the request size limit middleware that caused GET and DELETE requests to fail validation. The middleware incorrectly expected a request body (payload) for these methods and blocked them when none was present.

Example 3 (New feature):
<summary>Tyk Now Supports RSA-PSS Signed JWTs</summary>

Tyk now supports RSA-PSS signed JWTs (PS256, PS384, PS512), enhancing security while maintaining backward compatibility with RS256. No configuration changes are needed — just use RSA public keys, and Tyk will validate both algorithms seamlessly.
""".strip()

SYSTEM_PROMPT = f"""You are a technical writer for Tyk, an API gateway platform.
Your job is to transform Jira ticket information into polished, user-facing changelog entries for release notes.

Style guidelines:
- Write in third person, professional tone
- Be concise: the summary line should be a clear, actionable title (1 short sentence)
- The detail text should be 2-4 sentences explaining what changed and why it matters to users
- Use "Resolved", "Fixed", "Added", "Improved" etc. as appropriate
- Do NOT include the Jira ticket key in the text
- Do NOT use marketing language or exclamation marks
- Focus on the user impact, not the internal implementation details
- If the ticket is a bug fix, explain what was broken and how it's now fixed

Here are examples of well-written entries:

{EXAMPLE_ENTRIES}

Return your response in exactly this format (no markdown fences, no extra text):
SUMMARY: <the summary line text>
DETAIL: <the detail paragraph text>
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
                model=self.model, max_tokens=300,
                system="You are a technical writer for Tyk API Gateway. Write a brief Release Highlights section (2-4 sentences) summarizing the most important changes. Focus on user impact. Be concise and professional. Do not use bullet points. Do not start with 'This release'.",
                messages=[{"role": "user", "content": f"Changelog entries:\n{summaries}"}])
            return msg.content[0].text.strip()
        except Exception:
            logger.exception("Failed to generate release highlights")
            return 'This release focuses mainly on bug fixes. For a comprehensive list of changes, please refer to the detailed [changelog]({{< ref "#Changelog-vVERSION">}}) below.'

    def _call_api(self, ticket: Ticket, category: str) -> tuple[str, str]:
        parts = [f"Jira ticket: {ticket.key}", f"Issue type: {ticket.issue_type}", f"Category: {category}", f"Summary: {ticket.summary}"]
        if ticket.has_release_notes:
            parts.append(f"Release Notes field: {ticket.release_notes_text}")
        if ticket.description:
            parts.append(f"Description: {ticket.description[:1000]}")
        if ticket.is_breaking:
            parts.append(f"Breaking Change: {ticket.breaking_change}")
        msg = self.client.messages.create(model=self.model, max_tokens=500, system=SYSTEM_PROMPT, messages=[{"role": "user", "content": "\n".join(parts)}])
        text = msg.content[0].text.strip()
        summary_line = detail_text = ""
        for line in text.split("\n"):
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                summary_line = line[8:].strip()
            elif line.upper().startswith("DETAIL:"):
                detail_text = line[7:].strip()
        return summary_line or ticket.summary, detail_text or ticket.best_text
