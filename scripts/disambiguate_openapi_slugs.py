#!/usr/bin/env python3
"""
Disambiguate Mintlify OpenAPI page-slug collisions by suffixing operation summaries.

WHY: Mintlify builds every API reference page URL as
        /api-reference/<slug(first-tag)>/<slug(summary or operationId)>
in one global, flat namespace shared by ALL specs in docs.json. When two operations
(in the same or different specs) produce the same slug, Mintlify keeps one at the clean
URL and silently suffixes/drops the rest — so a page can render the wrong endpoint.
This is DX-2380 (Dashboard "Create a key" rendered the Admin /admin/org/keys endpoint).

WHAT THIS DOES: detects every colliding slug, keeps the first occurrence (discovery order:
docs.json spec order, then path, then method) at its clean slug, and appends an incrementing
integer to the *summary* of each subsequent colliding operation ("Create a key" -> "Create a
key 2"). That makes every slug unique (create-a-key, create-a-key-2, create-a-key-3 ...), so
every API group's nav links to its own correct page. Summaries (not tags) are suffixed so the
tag-based navigation grouping is preserved.

WHERE THIS RUNS: as a deploy-time step in .github/workflows/deploy-docs.yml, AFTER the docs
merger and BEFORE the deployment PR is created. It rewrites the swagger that gets deployed to
the `production` branch only — it never edits the auto-synced swagger/*.yml on `main`, so it is
compatible with the "do not edit auto-generated files" rule and re-applies on every deploy.

Editing is surgical: ruamel.yaml is used only to locate each target operation's `summary:`
line; the raw file text is then rewritten one line at a time so nothing else in the spec
changes (no reformatting, no re-wrapping of descriptions, no block-scalar normalisation).
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

from ruamel.yaml import YAML

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}


def slugify(text):
    text = (text or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def find_openapi_specs(docs_json_path):
    with open(docs_json_path, encoding="utf-8") as f:
        config = json.load(f)
    specs = []

    def walk(node):
        if isinstance(node, dict):
            spec = node.get("openapi")
            if isinstance(spec, str) and spec not in specs:
                specs.append(spec)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(config)
    return specs


def label_of(operation):
    return operation.get("summary") or operation.get("operationId") or ""


def slug_of(operation):
    tag = (operation.get("tags") or ["untagged"])[0]
    return f"{slugify(tag)}/{slugify(label_of(operation))}"


def rewrite_summary_line(line, new_value):
    """Rewrite a single 'summary: ...' line to new_value, preserving indentation and quote style.

    Returns the line unchanged if it isn't a simple single-line summary (e.g. a block scalar),
    so we never corrupt multi-line values.
    """
    newline = "\n" if line.endswith("\n") else ""
    body = line[:-1] if newline else line
    m = re.match(r"^(\s*summary:[ \t]+)(.*)$", body)
    if not m:
        return line
    prefix, raw = m.group(1), m.group(2).rstrip()
    if raw in (">", "|", "") or raw[0] in (">", "|", "&", "*"):
        return line  # block scalar / anchor — leave it alone
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        rebuilt = "'" + new_value.replace("'", "''") + "'"
    elif len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
        rebuilt = '"' + new_value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    else:
        rebuilt = new_value
    return prefix + rebuilt + newline


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", nargs="?", default=".", help="Repo root containing docs.json (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    docs_json_path = os.path.join(args.directory, "docs.json")
    if not os.path.isfile(docs_json_path):
        print(f"ERROR: docs.json not found in {args.directory}")
        return 2

    yaml = YAML()
    yaml.preserve_quotes = True

    specs = find_openapi_specs(docs_json_path)
    # discovery order: list of (spec_rel, path, method, operation)
    operations = []
    for spec_rel in specs:
        spec_path = os.path.join(args.directory, spec_rel)
        if not os.path.isfile(spec_path):
            print(f"  WARNING: spec referenced in docs.json not found: {spec_rel}")
            continue
        with open(spec_path, encoding="utf-8") as f:
            doc = yaml.load(f)
        for path, methods in (doc.get("paths") or {}).items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.lower() in HTTP_METHODS and isinstance(operation, dict):
                    operations.append((spec_rel, path, method, operation))

    groups = defaultdict(list)
    for entry in operations:
        groups[slug_of(entry[3])].append(entry)

    # Decide the new summary for each colliding operation (keep entries[0] clean).
    # edits_by_spec[spec_rel] = list of (line_index, new_summary_value)
    edits_by_spec = defaultdict(list)
    changed = []
    for slug, entries in groups.items():
        if len(entries) < 2:
            continue
        for n, (spec_rel, path, method, operation) in enumerate(entries[1:], start=2):
            old_label = label_of(operation)
            new_label = f"{old_label} {n}".strip()
            lc = operation.lc.data.get("summary")
            if lc is None:
                print(f"  WARNING: cannot locate 'summary:' line for {method.upper()} {path} "
                      f"in {spec_rel} (operationId-only); skipping.")
                continue
            value_line = lc[2]  # 0-indexed line of the summary value
            edits_by_spec[spec_rel].append((value_line, new_label))
            changed.append((spec_rel, method.upper(), path, slug, f"{slugify((operation.get('tags') or ['untagged'])[0])}/{slugify(new_label)}"))

    if not changed:
        print("✅ No colliding slugs — nothing to disambiguate.")
        return 0

    print(f"Disambiguated {len(changed)} colliding operation(s) across {len(edits_by_spec)} spec(s):")
    for spec_rel, method, path, old_slug, new_slug in changed:
        print(f"  [{spec_rel}] {method:6} {path}")
        print(f"      /api-reference/{old_slug}  ->  /api-reference/{new_slug}")

    if args.dry_run:
        print("\n(--dry-run: no files written)")
        return 0

    for spec_rel, edits in edits_by_spec.items():
        spec_path = os.path.join(args.directory, spec_rel)
        with open(spec_path, encoding="utf-8") as f:
            lines = f.readlines()
        for value_line, new_value in edits:
            lines[value_line] = rewrite_summary_line(lines[value_line], new_value)
        with open(spec_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    print(f"\nWrote {len(edits_by_spec)} updated spec file(s) (only summary lines changed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
