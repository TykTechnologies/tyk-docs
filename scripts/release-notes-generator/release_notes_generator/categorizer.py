"""Categorize Jira tickets into changelog categories."""

from __future__ import annotations

import logging

from release_notes_generator.config import COMPONENT_TO_PRODUCT, ISSUE_TYPE_TO_CATEGORY
from release_notes_generator.models import Ticket

logger = logging.getLogger(__name__)


def categorize_ticket(ticket: Ticket) -> str:
    if ticket.issue_type.lower() in ("security", "vulnerability"):
        return "Security Fixes"
    category = ISSUE_TYPE_TO_CATEGORY.get(ticket.issue_type, "Changed")
    logger.debug("Ticket %s (type=%s) -> '%s'", ticket.key, ticket.issue_type, category)
    return category


def group_tickets_by_component(tickets: list[Ticket]) -> dict[str, list[Ticket]]:
    groups: dict[str, list[Ticket]] = {}
    for ticket in tickets:
        matched = False
        for component in ticket.components:
            if component in COMPONENT_TO_PRODUCT:
                groups.setdefault(component, []).append(ticket)
                matched = True
        if not matched:
            logger.warning("Ticket %s has no recognized component (components=%s), skipping.", ticket.key, ticket.components)
    return groups
