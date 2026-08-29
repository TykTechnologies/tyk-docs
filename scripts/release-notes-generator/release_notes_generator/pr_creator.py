"""Git operations and GitHub PR creation."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class PRCreator:
    def __init__(self, repo_path: Path, github_token: str | None = None, target_branch: str | None = None):
        self.repo_path = repo_path
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self.target_branch = target_branch or os.environ.get("GITHUB_TARGET_BRANCH", "main")

    def prepare_branch(self, product: str, version: str) -> str:
        """Create and checkout a feature branch from the target branch.

        Uses 'git checkout -b' from current HEAD after fetching latest.
        Does NOT reset --hard to avoid destroying untracked files (like this tool itself).
        """
        branch_name = f"release-notes/{product}-{version}"

        # Fetch latest from remote.
        self._run_git("fetch", "origin", self.target_branch)

        # Create feature branch from the remote target branch.
        # If the branch already exists (previous run), delete and recreate
        # to avoid duplicating content from the prior insertion.
        try:
            self._run_git("branch", "-D", branch_name)
            logger.info("Deleted existing branch %s", branch_name)
        except subprocess.CalledProcessError:
            pass  # Branch didn't exist, that's fine.

        self._run_git("checkout", "-b", branch_name, f"origin/{self.target_branch}")

        logger.info("On branch: %s", branch_name)
        return branch_name

    def commit_and_push(self, branch_name: str, modified_files: list[Path], commit_message: str) -> None:
        for f in modified_files:
            rel_path = f.relative_to(self.repo_path)
            self._run_git("add", str(rel_path))
        self._run_git("commit", "-m", commit_message)
        self._run_git("push", "--force-with-lease", "-u", "origin", branch_name)

    def create_pr(self, branch_name: str, product: str, version: str, ticket_keys: list[str]) -> str | None:
        title = f"docs: Add release notes for {product.title()} v{version}"
        body = self._build_pr_body(product, version, ticket_keys)
        try:
            from github import Github
            if not self.github_token:
                raise ValueError("Set GITHUB_TOKEN.")
            gh = Github(self.github_token)
            repo = gh.get_repo(os.environ.get("GITHUB_REPO", "TykTechnologies/tyk-docs"))
            pr = repo.create_pull(title=title, body=body, head=branch_name, base=self.target_branch)
            try:
                pr.add_to_labels("release-notes", "automated")
            except Exception:
                logger.warning("Could not add labels")
            logger.info("PR created: %s", pr.html_url)
            return pr.html_url
        except Exception:
            logger.exception("Failed to create PR")
            return None

    def _build_pr_body(self, product: str, version: str, ticket_keys: list[str]) -> str:
        jira_base = "https://tyktech.atlassian.net/browse"
        tickets = "\n".join(f"- [{k}]({jira_base}/{k})" for k in sorted(ticket_keys))
        return f"""## Release Notes for {product.title()} v{version}

Auto-generated release notes from Jira tickets.

### Included Tickets

{tickets}

### Checklist

- [ ] Review changelog entries for accuracy
- [ ] Fill in Dependencies / Compatibility Matrix
- [ ] Verify Release Highlights summary
- [ ] Check Breaking Changes section
- [ ] Update Docker image links if needed
- [ ] Review and polish any AI-generated text
"""

    def _run_git(self, *args: str) -> str:
        cmd = ["git", *args]
        logger.debug("Running: %s", " ".join(cmd))
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True, check=True)
        return result.stdout.strip()
