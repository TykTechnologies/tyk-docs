"""Jira client for fetching tickets via Tyk AI Gateway REST API."""

from __future__ import annotations

import logging
import os

import requests

from release_notes_generator.config import (
    JIRA_API_BASE_URL, JIRA_BREAKING_CHANGE_FIELD, JIRA_INCLUDE_CHANGELOG_FIELD,
    JIRA_INSTANCE_URL, JIRA_PROJECT_KEY, JIRA_RELEASE_NOTES_FIELD,
)
from release_notes_generator.models import Ticket

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, api_token: str | None = None):
        self.api_token = api_token or os.environ.get("TYK_JIRA_API_TOKEN", "")
        if not self.api_token:
            raise ValueError("Set TYK_JIRA_API_TOKEN environment variable.")
        self.base_url = JIRA_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_token}", "Content-Type": "application/json"})

    def fetch_tickets(self, fix_version: str, component: str | None = None) -> list[Ticket]:
        jql = self._build_jql(fix_version, component)
        logger.info("Fetching tickets with JQL: %s", jql)
        fields = self._build_fields_list()
        tickets: list[Ticket] = []
        next_page_token: str | None = None
        while True:
            data = self._search(jql, fields, next_page_token)
            for issue in data.get("issues", []):
                ticket = self._parse_issue(issue)
                if ticket:
                    tickets.append(ticket)
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break
        logger.info("Fetched %d tickets", len(tickets))
        return tickets

    def _build_jql(self, fix_version: str, component: str | None) -> str:
        clauses = [f'project = {JIRA_PROJECT_KEY}', f'fixVersion = "{fix_version}"']
        if component:
            clauses.append(f'component = "{component}"')
        if JIRA_INCLUDE_CHANGELOG_FIELD:
            clauses.append(f'"{JIRA_INCLUDE_CHANGELOG_FIELD}" = "Yes"')
        return " AND ".join(clauses) + " ORDER BY issuetype ASC, key ASC"

    def _build_fields_list(self) -> str:
        fields = ["summary", "issuetype", "components", "fixVersions", "description"]
        for f in [JIRA_RELEASE_NOTES_FIELD, JIRA_BREAKING_CHANGE_FIELD, JIRA_INCLUDE_CHANGELOG_FIELD]:
            if f:
                fields.append(f)
        return ",".join(fields)

    def _search(self, jql: str, fields: str, next_page_token: str | None = None) -> dict:
        params: dict[str, list[str]] = {"jql": [jql], "fields": [fields], "maxResults": ["100"]}
        if next_page_token:
            params["nextPageToken"] = [next_page_token]
        body = {"operation_id": "searchAndReconsileIssuesUsingJql", "parameters": params}
        response = self.session.post(self.base_url, json=body)
        response.raise_for_status()
        return response.json()

    def _parse_issue(self, issue: dict) -> Ticket | None:
        fields = issue.get("fields", {})
        key = issue.get("key", "")
        summary = fields.get("summary", "")
        issue_type = fields.get("issuetype", {}).get("name", "Task")
        components = [c.get("name", "") for c in fields.get("components", []) if c.get("name")]
        release_notes_text = None
        if JIRA_RELEASE_NOTES_FIELD:
            rn = fields.get(JIRA_RELEASE_NOTES_FIELD)
            if isinstance(rn, str):
                release_notes_text = rn
            elif isinstance(rn, dict):
                release_notes_text = self._extract_adf_text(rn) if rn.get("type") == "doc" else (rn.get("value") or rn.get("text"))
        breaking_change = None
        if JIRA_BREAKING_CHANGE_FIELD:
            bc = fields.get(JIRA_BREAKING_CHANGE_FIELD)
            if isinstance(bc, dict):
                breaking_change = bc.get("value")
            elif isinstance(bc, str):
                breaking_change = bc
        description = fields.get("description")
        if isinstance(description, dict):
            description = self._extract_adf_text(description)
        return Ticket(key=key, summary=summary, issue_type=issue_type, components=components,
                      release_notes_text=release_notes_text, breaking_change=breaking_change, description=description)

    @staticmethod
    def _extract_adf_text(adf: dict) -> str:
        texts: list[str] = []
        def _walk(node):
            if isinstance(node, list):
                for item in node:
                    _walk(item)
            elif isinstance(node, dict):
                if node.get("type") == "text":
                    texts.append(node.get("text", ""))
                for child in node.get("content", []):
                    _walk(child)
        _walk(adf)
        return " ".join(texts).strip()

    def get_ticket_url(self, ticket_key: str) -> str:
        return f"{JIRA_INSTANCE_URL}/browse/{ticket_key}"
