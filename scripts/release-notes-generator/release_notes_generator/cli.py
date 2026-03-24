"""CLI entry point for the release notes generator."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from release_notes_generator.ai_enhancer import AIEnhancer
from release_notes_generator.categorizer import categorize_ticket, group_tickets_by_component
from release_notes_generator.config import PRODUCT_ARG_TO_COMPONENT, get_component_for_product, get_product_config
from release_notes_generator.file_inserter import get_release_notes_path, insert_release_section
from release_notes_generator.jira_client import JiraClient
from release_notes_generator.models import ChangelogEntry, ReleaseSection
from release_notes_generator.pr_creator import PRCreator
from release_notes_generator.renderer import render_release_section

logger = logging.getLogger(__name__)


def extract_semver(fix_version: str) -> str:
    match = re.search(r"(\d+\.\d+\.\d+)", fix_version)
    return match.group(1) if match else fix_version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="release-notes-generator", description="Generate Tyk release notes from Jira tickets.")
    parser.add_argument("--fix-version", required=True, help="Jira fix version (e.g., 'Tyk 5.8.0').")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--product", choices=list(PRODUCT_ARG_TO_COMPONENT.keys()))
    group.add_argument("--all-products", action="store_true")
    parser.add_argument("--release-date", required=True, help="'DD Month YYYY' format.")
    parser.add_argument("--repo-path", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-ai", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser


def resolve_repo_path(args_repo_path: Path | None) -> Path:
    if args_repo_path:
        return args_repo_path.resolve()
    script_dir = Path(__file__).resolve().parent
    repo_path = script_dir.parent.parent.parent
    if (repo_path / "developer-support").exists():
        return repo_path
    if (Path.cwd() / "developer-support").exists():
        return Path.cwd()
    logger.error("Cannot auto-detect tyk-docs repo root. Use --repo-path.")
    sys.exit(1)


def generate_for_product(product_arg, tickets, fix_version, release_date, repo_path, dry_run, no_ai, pr_creator):
    pc = get_product_config(product_arg)
    logger.info("Generating release notes for %s (%d tickets)", pc.label, len(tickets))
    categorized = [(t, categorize_ticket(t)) for t in tickets]
    if no_ai:
        entries = [ChangelogEntry(ticket_key=t.key, category=c, summary_line=t.summary, detail_text=t.best_text,
                                  is_breaking=t.is_breaking, breaking_description=t.breaking_change) for t, c in categorized]
        highlights = ""
    else:
        enhancer = AIEnhancer()
        entries = enhancer.enhance_tickets(categorized)
        highlights = enhancer.generate_release_highlights(entries)
    semver = extract_semver(fix_version)
    section = ReleaseSection(version=semver, release_date=release_date, product=product_arg, product_label=pc.label, entries=entries)
    rn_path = get_release_notes_path(repo_path, pc.file)
    if not rn_path.exists():
        logger.error("Release notes file not found: %s", rn_path)
        sys.exit(1)
    content = rn_path.read_text(encoding="utf-8")
    is_new_minor = f"## {section.major_minor} Release Notes" not in content
    rendered = render_release_section(section, release_highlights=highlights, is_new_minor=is_new_minor)
    if dry_run:
        print(f"\n{'='*60}\nRelease Notes for {pc.label} v{semver}\n{'='*60}\n")
        print(rendered)
        return None
    modified = insert_release_section(rn_path, rendered, semver)
    rn_path.write_text(modified, encoding="utf-8")
    logger.info("Updated %s", rn_path)
    return rn_path


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")
    repo_path = resolve_repo_path(args.repo_path)
    logger.info("Using repo path: %s", repo_path)
    jira = JiraClient()
    if args.all_products:
        tickets = jira.fetch_tickets(args.fix_version)
        groups = group_tickets_by_component(tickets)
        if not groups:
            logger.error("No tickets found for %s", args.fix_version)
            sys.exit(1)
        logger.info("Found tickets for %d products: %s", len(groups), ", ".join(groups.keys()))
    else:
        comp = get_component_for_product(args.product)
        tickets = jira.fetch_tickets(args.fix_version, comp)
        if not tickets:
            logger.error("No tickets found for %s %s", comp, args.fix_version)
            sys.exit(1)
        groups = {comp: tickets}

    semver = extract_semver(args.fix_version)
    product_label = args.product or "all"
    pr_creator = None
    branch_name = None
    if not args.dry_run:
        pr_creator = PRCreator(repo_path)
        branch_name = pr_creator.prepare_branch(product_label, semver)

    modified_files: list[Path] = []
    all_keys: list[str] = []
    for comp_name, comp_tickets in groups.items():
        product_arg = next((a for a, c in PRODUCT_ARG_TO_COMPONENT.items() if c == comp_name), None)
        if not product_arg:
            logger.warning("No CLI mapping for %s, skipping", comp_name)
            continue
        path = generate_for_product(product_arg, comp_tickets, args.fix_version, args.release_date, repo_path, args.dry_run, args.no_ai, pr_creator)
        if path:
            modified_files.append(path)
        all_keys.extend(t.key for t in comp_tickets)

    if not args.dry_run and modified_files and pr_creator and branch_name:
        pr_creator.commit_and_push(branch_name, modified_files, f"docs: Add release notes for {product_label.title()} v{semver}")
        pr_url = pr_creator.create_pr(branch_name=branch_name, product=product_label, version=semver, ticket_keys=all_keys)
        if pr_url:
            print(f"\nPR created: {pr_url}")
        else:
            logger.error("Failed to create PR")
            sys.exit(1)


if __name__ == "__main__":
    main()
