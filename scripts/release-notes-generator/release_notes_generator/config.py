"""Configuration constants and product mappings."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductConfig:
    file: str
    docker: str | None
    label: str
    source_repo: str | None = None


COMPONENT_TO_PRODUCT: dict[str, ProductConfig] = {
    "Tyk Gateway": ProductConfig(file="gateway.mdx", docker="tykio/tyk-gateway", label="Gateway", source_repo="TykTechnologies/tyk"),
    "Tyk Dashboard": ProductConfig(file="dashboard.mdx", docker="tykio/tyk-dashboard", label="Dashboard"),
    "MDCB": ProductConfig(file="mdcb.mdx", docker="tykio/tyk-mdcb-docker", label="MDCB"),
    "Tyk Pump": ProductConfig(file="pump.mdx", docker="tykio/tyk-pump-docker-pub", label="Pump", source_repo="TykTechnologies/tyk-pump"),
    "Tyk Operator": ProductConfig(file="operator.mdx", docker=None, label="Operator"),
    "Tyk Sync": ProductConfig(file="sync.mdx", docker=None, label="Sync"),
}

PRODUCT_ARG_TO_COMPONENT: dict[str, str] = {
    "gateway": "Tyk Gateway",
    "dashboard": "Tyk Dashboard",
    "mdcb": "MDCB",
    "pump": "Tyk Pump",
    "operator": "Tyk Operator",
    "sync": "Tyk Sync",
}

ISSUE_TYPE_TO_CATEGORY: dict[str, str] = {
    "Bug": "Fixed",
    "Story": "Added",
    "New Feature": "Added",
    "Task": "Changed",
    "Improvement": "Changed",
    "Sub-task": "Changed",
}

JIRA_PROJECT_KEY = "TT"
JIRA_API_BASE_URL = "https://ai-gateway.tyk.technology/tools/tyk-jira-search"
JIRA_INSTANCE_URL = "https://tyktech.atlassian.net"

JIRA_RELEASE_NOTES_FIELD = os.environ.get("JIRA_RELEASE_NOTES_FIELD", "customfield_10338")
JIRA_INCLUDE_CHANGELOG_FIELD = os.environ.get("JIRA_INCLUDE_CHANGELOG_FIELD", "customfield_10335")
JIRA_BREAKING_CHANGE_FIELD = os.environ.get("JIRA_BREAKING_CHANGE_FIELD", "customfield_10684")

ANTHROPIC_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://ai-gateway.tyk.technology/llm/call/anthropic-gateway")

RELEASE_NOTES_DIR = "developer-support/release-notes"

GITHUB_REPO = "TykTechnologies/tyk-docs"
GITHUB_TARGET_BRANCH = os.environ.get("GITHUB_TARGET_BRANCH", "main")


def get_product_config(product_arg: str) -> ProductConfig:
    component = PRODUCT_ARG_TO_COMPONENT.get(product_arg)
    if not component:
        raise ValueError(f"Unknown product '{product_arg}'. Valid: {', '.join(PRODUCT_ARG_TO_COMPONENT.keys())}")
    return COMPONENT_TO_PRODUCT[component]


def get_component_for_product(product_arg: str) -> str:
    component = PRODUCT_ARG_TO_COMPONENT.get(product_arg)
    if not component:
        raise ValueError(f"Unknown product '{product_arg}'.")
    return component
