"""CLI entry point for the release notes generator."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from release_notes_generator.ai_enhancer import AIEnhancer
from release_notes_generator.categorizer import categorize_ticket, group_tickets_by_component
from release_notes_generator.config import PRODUCT_ARG_TO_COMPONENT, get_component_for_product, get_product_config
from release_notes_generator.file_inserter import get_release_notes_path, insert_release_section
from release_notes_generator.jira_client import JiraClient
from release_notes_generator.models import ChangelogEntry, ReleaseSection
from release_notes_generator.pr_creator import PRCreator
from release_notes_generator.renderer import render_release_section

logger = logging.getLogger(__name__)
console = Console()

BANNER = """[bold cyan]
 ___      _                    _  _     _
| _ \\__ _| |___ __ _ ___ ___  | \\| |___| |_ ___ ___
|   / -_| / -_)/ _` (_-</ -_) | .` / _ \\  _/ -_|_-<
|_|_\\___|_\\___|\\__,_/__/\\___| |_|\\_\\___/\\__\\___/__/
                                    [dim]Generator[/dim]
[/bold cyan]"""


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
    console.print("[red]Cannot auto-detect tyk-docs repo root. Use --repo-path.[/red]")
    sys.exit(1)


def print_config(args, semver: str) -> None:
    """Print a nice configuration summary."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bold")
    table.add_row("Fix Version", args.fix_version)
    table.add_row("Semver", semver)
    table.add_row("Product", args.product or "all products")
    table.add_row("Release Date", args.release_date)
    table.add_row("Mode", "[yellow]Dry Run[/yellow]" if args.dry_run else "[green]Live (PR)[/green]")
    table.add_row("AI Enhancement", "[red]Disabled[/red]" if args.no_ai else "[green]Enabled (Claude)[/green]")
    console.print(Panel(table, title="[bold]Configuration[/bold]", border_style="cyan"))


def print_tickets_summary(groups: dict) -> None:
    """Print a tree of fetched tickets grouped by product."""
    tree = Tree("[bold]Jira Tickets[/bold]")
    total = 0
    for comp_name, tickets in groups.items():
        product_branch = tree.add(f"[bold cyan]{comp_name}[/bold cyan] ({len(tickets)} tickets)")
        for t in tickets:
            icon = {"Bug": "[red]B[/red]", "Story": "[green]S[/green]", "Task": "[yellow]T[/yellow]"}.get(t.issue_type, "[dim]?[/dim]")
            product_branch.add(f"{icon} [dim]{t.key}[/dim] {t.summary[:70]}")
        total += len(tickets)
    console.print(Panel(tree, title=f"[bold]{total} tickets found[/bold]", border_style="green"))


def enhance_with_progress(categorized: list, no_ai: bool) -> tuple[list[ChangelogEntry], str]:
    """Enhance tickets with a nice progress display."""
    if no_ai:
        entries = [
            ChangelogEntry(
                ticket_key=t.key, category=c, summary_line=t.summary,
                detail_text=t.best_text, is_breaking=t.is_breaking,
                breaking_description=t.breaking_change,
            )
            for t, c in categorized
        ]
        return entries, ""

    enhancer = AIEnhancer()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Enhancing tickets with Claude AI...", total=len(categorized))

        results: dict[int, ChangelogEntry] = {}

        def _on_complete(idx: int, entry: ChangelogEntry) -> None:
            results[idx] = entry
            progress.advance(task)

        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(enhancer.enhance_ticket, t, c): i
                for i, (t, c) in enumerate(categorized)
            }
            for future in as_completed(futures):
                idx = futures[future]
                entry = future.result()
                _on_complete(idx, entry)

        entries = [results[i] for i in range(len(categorized))]

    console.print("[green]  AI enhancement complete[/green]")

    with console.status("[cyan]Generating release highlights...[/cyan]"):
        highlights = enhancer.generate_release_highlights(entries)

    console.print("[green]  Release highlights generated[/green]")
    return entries, highlights


def print_changelog_summary(entries: list[ChangelogEntry]) -> None:
    """Print a summary of categorized entries."""
    table = Table(title="Changelog Summary", border_style="dim")
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Entries")

    categories = {}
    for e in entries:
        categories.setdefault(e.category, []).append(e)

    colors = {"Added": "green", "Fixed": "red", "Changed": "yellow", "Security Fixes": "magenta"}
    for cat in ["Added", "Changed", "Fixed", "Security Fixes"]:
        if cat in categories:
            items = categories[cat]
            previews = ", ".join(e.summary_line[:40] for e in items[:3])
            if len(items) > 3:
                previews += f" [dim]+{len(items) - 3} more[/dim]"
            table.add_row(f"[{colors.get(cat, 'white')}]{cat}[/]", str(len(items)), previews)

    console.print(table)


def generate_for_product(product_arg, tickets, fix_version, release_date, repo_path, dry_run, no_ai, pr_creator):
    pc = get_product_config(product_arg)
    semver = extract_semver(fix_version)

    console.print(f"\n[bold cyan]--- {pc.label} v{semver} ---[/bold cyan]")

    categorized = [(t, categorize_ticket(t)) for t in tickets]
    entries, highlights = enhance_with_progress(categorized, no_ai)

    print_changelog_summary(entries)

    section = ReleaseSection(
        version=semver, release_date=release_date,
        product=product_arg, product_label=pc.label, entries=entries,
    )
    rn_path = get_release_notes_path(repo_path, pc.file)
    if not rn_path.exists():
        console.print(f"[red]Release notes file not found: {rn_path}[/red]")
        sys.exit(1)

    content = rn_path.read_text(encoding="utf-8")
    is_new_minor = f"## {section.major_minor} Release Notes" not in content
    rendered = render_release_section(section, release_highlights=highlights, is_new_minor=is_new_minor)

    if dry_run:
        console.print(Panel(rendered, title=f"[bold]{pc.label} v{semver}[/bold]", border_style="green", subtitle="[dim]DRY RUN[/dim]"))
        return None

    modified = insert_release_section(rn_path, rendered, semver)
    rn_path.write_text(modified, encoding="utf-8")
    console.print(f"[green]  Updated {rn_path.name}[/green]")
    return rn_path


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Suppress noisy loggers in pretty mode; keep them for --verbose.
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    console.print(BANNER)

    semver = extract_semver(args.fix_version)
    repo_path = resolve_repo_path(args.repo_path)
    print_config(args, semver)

    # --- Fetch from Jira ---
    with console.status("[bold cyan]Fetching tickets from Jira...[/bold cyan]"):
        jira = JiraClient()
        if args.all_products:
            tickets = jira.fetch_tickets(args.fix_version)
            groups = group_tickets_by_component(tickets)
        else:
            comp = get_component_for_product(args.product)
            tickets = jira.fetch_tickets(args.fix_version, comp)
            groups = {comp: tickets} if tickets else {}

    if not groups:
        console.print("[red]No tickets found. Check the fix version and try again.[/red]")
        sys.exit(1)

    # Filter out empty groups.
    groups = {k: v for k, v in groups.items() if v}
    print_tickets_summary(groups)

    # --- Prepare branch ---
    product_label = args.product or "all"
    pr_creator = None
    branch_name = None
    if not args.dry_run:
        with console.status("[bold cyan]Preparing git branch...[/bold cyan]"):
            pr_creator = PRCreator(repo_path)
            branch_name = pr_creator.prepare_branch(product_label, semver)
        console.print(f"[green]  Branch: {branch_name}[/green]")

    # --- Generate for each product ---
    modified_files: list[Path] = []
    all_keys: list[str] = []

    for comp_name, comp_tickets in groups.items():
        product_arg = next((a for a, c in PRODUCT_ARG_TO_COMPONENT.items() if c == comp_name), None)
        if not product_arg:
            console.print(f"[yellow]  Skipping {comp_name} (no CLI mapping)[/yellow]")
            continue

        path = generate_for_product(
            product_arg, comp_tickets, args.fix_version,
            args.release_date, repo_path, args.dry_run, args.no_ai, pr_creator,
        )
        if path:
            modified_files.append(path)
        all_keys.extend(t.key for t in comp_tickets)

    # --- Create PR ---
    if not args.dry_run and modified_files and pr_creator and branch_name:
        with console.status("[bold cyan]Pushing and creating PR...[/bold cyan]"):
            pr_creator.commit_and_push(
                branch_name, modified_files,
                f"docs: Add release notes for {product_label.title()} v{semver}",
            )
            pr_url = pr_creator.create_pr(
                branch_name=branch_name, product=product_label,
                version=semver, ticket_keys=all_keys,
            )

        if pr_url:
            console.print()
            console.print(Panel(
                f"[bold green]{pr_url}[/bold green]",
                title="[bold]PR Created[/bold]",
                border_style="green",
            ))
        else:
            console.print("[red]Failed to create PR.[/red]")
            sys.exit(1)

    if args.dry_run:
        console.print()
        console.print("[bold yellow]Dry run complete. No files were modified.[/bold yellow]")

    console.print()


if __name__ == "__main__":
    main()
