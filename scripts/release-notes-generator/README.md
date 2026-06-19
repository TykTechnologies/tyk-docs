# Release Notes Generator

Automatically generates release notes for Tyk products by pulling Jira tickets and using Claude AI to write polished, user-facing changelog entries. The output matches the exact format used in the tyk-docs MDX release notes files.

## What It Does

1. **Fetches tickets from Jira** — queries by fix version (e.g., `"Tyk 5.13.0"`) via the Tyk AI Gateway, filtering only tickets where `Include in changelog? = Yes`
2. **Detects products automatically** — groups tickets by their Jira component (Gateway, Dashboard, Portal, etc.). Tickets without a component are inferred from the fix version name
3. **Categorizes entries** — maps Jira issue types to changelog sections: Bug → Fixed, Story → Added, Task → Changed. Stories with update/upgrade keywords are reclassified as Changed
4. **Polishes text with Claude AI** — each ticket is sent to Claude (via Tyk AI Gateway) which generates a summary title and detailed description following Tyk's writing style. Tickets are processed in parallel for speed
5. **Generates release highlights** — AI writes a brief overview of the most important changes
6. **Renders into MDX format** — produces the exact `<AccordionGroup>/<Accordion>` format used in tyk-docs release notes
7. **Inserts into existing files** — parses the current `.mdx` release notes file and inserts the new version section at the correct position (reverse chronological order)
8. **Creates a PR** — pushes a branch and opens a pull request on tyk-docs with a checklist for reviewers

## Quick Start

```bash
cd scripts/release-notes-generator
pip install -r requirements.txt
```

### Environment Variables

```bash
# Required — Tyk AI Gateway token (used for both Jira search and Claude API)
export TYK_JIRA_API_TOKEN="your-token"

# Required only for PR creation (not needed with --dry-run)
export GITHUB_TOKEN="your-github-token"
```

### Usage

```bash
# Preview what will be generated (no files modified, no PR)
python3 -m release_notes_generator \
  --fix-version "Tyk 5.13.0" \
  --release-date "24 March 2026" \
  --dry-run

# Generate release notes and create a PR
python3 -m release_notes_generator \
  --fix-version "Tyk Portal 1.17.1" \
  --release-date "24 March 2026"

# Skip AI enhancement (use raw Jira data)
python3 -m release_notes_generator \
  --fix-version "Tyk 5.13.0" \
  --release-date "24 March 2026" \
  --dry-run --no-ai
```

### CLI Options

| Flag | Description |
|---|---|
| `--fix-version` | Jira fix version name (e.g., `"Tyk 5.13.0"`, `"Tyk Portal 1.17.1"`) |
| `--release-date` | Release date in `"DD Month YYYY"` format |
| `--dry-run` | Print output to terminal without modifying files or creating a PR |
| `--no-ai` | Skip Claude AI enhancement, use raw Jira ticket data |
| `--repo-path` | Path to tyk-docs repo root (auto-detected if omitted) |
| `--verbose` | Enable debug logging |

Products are auto-detected from the tickets' Jira components — no need to specify which product to generate for.

## GitHub Action

A `workflow_dispatch` action is included at `.github/workflows/generate-release-notes.yml`. After merging to `main`:

1. Go to **Actions** > **Generate Release Notes** > **Run workflow**
2. Fill in:
   - **Fix Version**: e.g., `Tyk 5.13.0`
   - **Release Date**: e.g., `24 March 2026`

### Required Secrets

| Secret | Description |
|---|---|
| `TYK_JIRA_API_TOKEN` | Bearer token for the Tyk AI Gateway (handles both Jira search and Claude API) |

`GITHUB_TOKEN` is provided automatically by GitHub Actions.

## Supported Products

| Jira Component(s) | Release Notes File | Docker Image |
|---|---|---|
| Tyk Gateway, Gateway | `gateway.mdx` | `tykio/tyk-gateway` |
| Tyk Dashboard | `dashboard.mdx` | `tykio/tyk-dashboard` |
| MDCB, Tyk MDCB | `mdcb.mdx` | `tykio/tyk-mdcb-docker` |
| Tyk Pump | `pump.mdx` | `tykio/tyk-pump-docker-pub` |
| Tyk Operator | `operator.mdx` | — |
| Tyk Sync | `sync.mdx` | — |
| Tyk Portal, Tyk Portal (old) | `portal.mdx` | `tykio/portal` |
| Tyk Charts | `helm-chart.mdx` | — |

Tickets without a Jira component are automatically assigned based on the fix version name (e.g., `"Tyk Portal 1.17.1"` → Portal).

## How Categorization Works

| Jira Issue Type | Changelog Section | Notes |
|---|---|---|
| Bug | Fixed | — |
| Story | Added | Reclassified to **Changed** if summary contains update/upgrade/bump/migrate/replace |
| New Feature | Added | Same override rule as Story |
| Task | Changed | — |
| Improvement | Changed | — |
| Security / Vulnerability | Security Fixes | — |

## Output Format

The tool renders changelog entries using the modern tyk-docs MDX component format:

```mdx
##### Added

<AccordionGroup>

<Accordion title='Added Client Certificate-Token Binding for Auth Token APIs'>
This release introduces the ability to bind client certificates to Auth Tokens
for APIs secured with a static mTLS allow list.

- Added a new `mtls_static_certificate_bindings` field to the session object.
- Supports binding multiple client certificates to a single key for certificate rotation.

This feature maintains full backward compatibility with existing keys.
</Accordion>

</AccordionGroup>
```

## Jira Fields Used

| Field | Custom Field ID | Purpose |
|---|---|---|
| Fix Version | *(built-in)* | Determines which release to query |
| Components | *(built-in)* | Maps tickets to products (e.g., Tyk Gateway → `gateway.mdx`) |
| Issue Type | *(built-in)* | Categorization: Bug → Fixed, Story → Added, Task → Changed |
| Include in changelog? | `customfield_10335` | Only tickets with value "Yes" are included |
| Release Notes* | `customfield_10338` | Human-written release note text (preferred over ticket summary when available) |
| Breaking Change | `customfield_10684` | Populates the Breaking Changes section |

## AI Enhancement

Each ticket is sent to Claude (Sonnet) with a system prompt that includes:

- 6 real examples from existing gateway.mdx release notes
- Style guidelines: past-tense verbs, backticks for config fields, bug fix structure (broken → impact → fixed)
- Support for multi-paragraph responses with bullet lists

The AI also generates a **Release Highlights** section summarizing the 2-4 most important changes in the release.

AI calls are parallelized (5 concurrent workers) for speed. If a call fails, the tool falls back to using the raw Jira ticket summary.

## Architecture

```
release_notes_generator/
  __main__.py       Entry point for python -m
  cli.py            CLI orchestration with rich terminal UI
  config.py         Product mappings, Jira field IDs, API endpoints
  models.py         Dataclasses: Ticket, ChangelogEntry, ReleaseSection
  jira_client.py    Fetches tickets via Tyk AI Gateway (POST + JQL)
  categorizer.py    Issue type -> category mapping + keyword overrides + component inference
  ai_enhancer.py    Claude API for polishing entries (parallel, with fallback)
  renderer.py       Renders into AccordionGroup/Accordion MDX format
  file_inserter.py  Parses existing .mdx files, inserts new version at correct position
  pr_creator.py     Git branch creation + commit + push + GitHub PR via PyGithub
```

## Running Tests

```bash
cd scripts/release-notes-generator
python3 -m pytest tests/ -v
```

46 tests covering categorization, rendering, and file insertion logic.
