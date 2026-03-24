# Release Notes Generator

Automated release notes generation for Tyk products. Fetches Jira tickets, uses AI to write polished changelog entries, and creates a PR on tyk-docs.

## How It Works

```
Jira (Tyk AI Gateway)          Claude AI                    tyk-docs
       |                           |                           |
  1. Fetch tickets            3. Polish each              5. Insert into
     by fix version              ticket into a               existing .mdx
     + "Include in               user-facing                 release notes
     changelog = Yes"            changelog entry              file
       |                           |                           |
  2. Categorize               4. Generate release         6. Create PR
     Bug -> Fixed                highlights summary
     Story -> Added
     Task -> Changed
```

## Quick Start

```bash
cd scripts/release-notes-generator
pip install -r requirements.txt

# Set the Tyk AI Gateway token (used for both Jira and Claude)
export TYK_JIRA_API_TOKEN="your-token"

# Preview (dry run, no PR created)
python3 -m release_notes_generator \
  --fix-version "Tyk 5.13.0" \
  --product dashboard \
  --release-date "24 March 2026" \
  --dry-run

# Generate for all products and create a PR
export GITHUB_TOKEN="your-github-token"
python3 -m release_notes_generator \
  --fix-version "Tyk 5.13.0" \
  --all-products \
  --release-date "24 March 2026"
```

## CLI Options

| Flag | Description |
|---|---|
| `--fix-version` | Jira fix version name (e.g., `"Tyk 5.13.0"`) |
| `--product` | Single product: `gateway`, `dashboard`, `mdcb`, `pump`, `operator`, `sync` |
| `--all-products` | Generate for all products that have tickets |
| `--release-date` | Release date in `"DD Month YYYY"` format |
| `--dry-run` | Print output to terminal, don't modify files or create PR |
| `--no-ai` | Skip Claude AI enhancement, use raw Jira data |
| `--repo-path` | Path to tyk-docs repo root (auto-detected if omitted) |
| `--verbose` | Enable debug logging |

## GitHub Action

Trigger manually from **Actions > Generate Release Notes > Run workflow**.

Inputs:
- **Fix Version**: e.g., `Tyk 5.13.0`
- **Product**: `all`, `gateway`, `dashboard`, etc.
- **Release Date**: e.g., `24 March 2026`

### Required Secrets

| Secret | Description |
|---|---|
| `TYK_JIRA_API_TOKEN` | Bearer token for Tyk AI Gateway (handles both Jira search and Claude API) |

`GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Architecture

```
release_notes_generator/
  cli.py            CLI with rich terminal UI
  config.py         Product mappings, Jira field IDs, API endpoints
  jira_client.py    Fetches tickets via Tyk AI Gateway (POST + JQL)
  categorizer.py    Issue type -> changelog category mapping
  ai_enhancer.py    Claude API for polishing entries (parallel)
  renderer.py       Renders into tyk-docs HTML/mdx format
  file_inserter.py  Parses existing .mdx, inserts new version section
  pr_creator.py     Git branch + commit + GitHub PR creation
  models.py         Ticket, ChangelogEntry, ReleaseSection dataclasses
```

## Jira Fields Used

| Field | ID | Purpose |
|---|---|---|
| Fix Version | built-in | Which release to query |
| Components | built-in | Maps to product (Tyk Gateway -> gateway.mdx) |
| Issue Type | built-in | Categorization (Bug->Fixed, Story->Added) |
| Include in changelog? | `customfield_10335` | Only tickets with "Yes" are included |
| Release Notes* | `customfield_10338` | Human-written text (preferred over summary) |
| Breaking Change | `customfield_10684` | Populates Breaking Changes section |

## Tests

```bash
python3 -m pytest tests/ -v
```
