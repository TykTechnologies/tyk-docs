"""Categorize Jira tickets into changelog categories."""

from __future__ import annotations

import logging

from release_notes_generator.config import COMPONENT_TO_PRODUCT, ISSUE_TYPE_TO_CATEGORY
from release_notes_generator.models import Ticket

logger = logging.getLogger(__name__)

# Maps keywords in fix version names to Jira component names.
# Used as fallback when a ticket has no component set.
_FIX_VERSION_TO_COMPONENT: dict[str, str] = {
    "portal": "Tyk Portal",
    "gateway": "Tyk Gateway",
    "dashboard": "Tyk Dashboard",
    "mdcb": "MDCB",
    "pump": "Tyk Pump",
    "operator": "Tyk Operator",
    "sync": "Tyk Sync",
    "chart": "Tyk Charts",
    "helm": "Tyk Charts",
}


def categorize_ticket(ticket: Ticket) -> str:
    if ticket.issue_type.lower() in ("security", "vulnerability"):
        return "Security Fixes"
    category = ISSUE_TYPE_TO_CATEGORY.get(ticket.issue_type, "Changed")
    logger.debug("Ticket %s (type=%s) -> '%s'", ticket.key, ticket.issue_type, category)
    return category


def infer_component_from_fix_version(fix_version: str) -> str | None:
    """Infer the Jira component name from the fix version string.

    E.g., "Tyk Portal 1.17.1" -> "Tyk Portal"
          "Tyk 5.13.0"        -> None (ambiguous, could be any product)
    """
    fv_lower = fix_version.lower()
    for keyword, component in _FIX_VERSION_TO_COMPONENT.items():
        if keyword in fv_lower:
            return component
    return None


def group_tickets_by_component(
    tickets: list[Ticket],
    fix_version: str = "",
) -> dict[str, list[Ticket]]:
    """Group tickets by Jira component.

    Tickets with no recognized component are assigned based on the fix version
    name as a fallback (e.g., "Tyk Portal 1.17.1" implies Tyk Portal).
    """
    fallback_component = infer_component_from_fix_version(fix_version) if fix_version else None
    groups: dict[str, list[Ticket]] = {}

    for ticket in tickets:
        matched = False
        for component in ticket.components:
            if component in COMPONENT_TO_PRODUCT:
                groups.setdefault(component, []).append(ticket)
                matched = True

        if not matched:
            if fallback_component and fallback_component in COMPONENT_TO_PRODUCT:
                logger.info(
                    "Ticket %s has no component, inferred '%s' from fix version.",
                    ticket.key, fallback_component,
                )
                groups.setdefault(fallback_component, []).append(ticket)
            else:
                logger.warning(
                    "Ticket %s has no recognized component (components=%s), skipping.",
                    ticket.key, ticket.components,
                )

    return groups
