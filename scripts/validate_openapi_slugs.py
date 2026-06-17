#!/usr/bin/env python3
"""
Detect Mintlify OpenAPI page-slug collisions across all specs referenced in docs.json.

Mintlify auto-generates one API reference page per OpenAPI operation. The page URL is
derived from the operation's *first tag* and its *summary* (falling back to operationId),
slugified as:  api-reference/<slug(tag)>/<slug(summary)>

All specs share a single flat /api-reference/ namespace, so two operations in *different*
specs that share a tag (case-insensitively) AND a summary collide to the same URL. At build
time one silently overwrites the other, so a page can render the wrong endpoint.

This is the root cause of DX-2380: the Dashboard API "Create a key." (tag "Keys") and the
Dashboard Admin API "Create a key." (tag "keys") both resolve to api-reference/keys/create-a-key.

Exit code 1 if any cross-spec collision is found (CI-failing). Within-spec duplicates are
reported as warnings (Mintlify resolves them, but they signal latent ambiguity).
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

import yaml

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}


def slugify(text):
    """Mirror Mintlify's slug rule: lowercase, non-alphanumerics to hyphens, trim."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def find_openapi_specs(docs_json_path):
    """Walk docs.json and return every distinct value of an "openapi" key (in order)."""
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


def operation_slug(tag, operation):
    """api-reference page slug Mintlify assigns: <slug(tag)>/<slug(summary or operationId)>."""
    label = operation.get("summary") or operation.get("operationId") or ""
    return f"{slugify(tag)}/{slugify(label)}"


def collect_slugs(root, specs):
    """Return slug -> list of {spec, method, path, tag, summary} occurrences."""
    slug_map = defaultdict(list)
    for spec_rel in specs:
        spec_path = os.path.join(root, spec_rel)
        if not os.path.isfile(spec_path):
            print(f"  WARNING: spec referenced in docs.json not found: {spec_rel}")
            continue
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        for path, methods in (spec.get("paths") or {}).items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                    continue
                # Mintlify groups an operation under its FIRST tag (that drives the URL).
                tags = operation.get("tags") or ["untagged"]
                tag = tags[0]
                slug_map[operation_slug(tag, operation)].append({
                    "spec": spec_rel,
                    "method": method.upper(),
                    "path": path,
                    "tag": tag,
                    "summary": operation.get("summary") or operation.get("operationId") or "",
                })
    return slug_map


def load_baseline(path):
    """Load a baseline file of known/accepted colliding slugs (one slug per line, # comments ok)."""
    if not path or not os.path.isfile(path):
        return set()
    allowed = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                allowed.add(line.lstrip("/").removeprefix("api-reference/"))
    return allowed


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", nargs="?", default=".", help="Repo root containing docs.json (default: .)")
    parser.add_argument("--baseline", metavar="FILE",
                        help="File of already-known colliding slugs to ignore (ratchet: fail only on NEW collisions)")
    parser.add_argument("--write-baseline", metavar="FILE",
                        help="Write all current cross-spec collisions to FILE as a baseline and exit 0")
    parser.add_argument("--warn-only", action="store_true",
                        help="Report collisions but always exit 0 (for staged rollout)")
    args = parser.parse_args()

    docs_json_path = os.path.join(args.directory, "docs.json")
    if not os.path.isfile(docs_json_path):
        print(f"ERROR: docs.json not found in {args.directory}")
        return 2

    specs = find_openapi_specs(docs_json_path)
    print(f"Found {len(specs)} OpenAPI spec(s) referenced in docs.json:")
    for s in specs:
        print(f"  - {s}")

    slug_map = collect_slugs(args.directory, specs)

    cross_spec = {}
    within_spec = {}
    for slug, occ in slug_map.items():
        distinct_specs = {o["spec"] for o in occ}
        if len(distinct_specs) > 1:
            cross_spec[slug] = occ
        elif len(occ) > 1:
            within_spec[slug] = occ

    if args.write_baseline:
        with open(args.write_baseline, "w", encoding="utf-8") as f:
            f.write("# Known OpenAPI page-slug collisions accepted as a baseline (DX-2380).\n")
            f.write("# New collisions outside this list fail CI. Drive this list down to zero.\n")
            for slug in sorted(cross_spec):
                f.write(f"api-reference/{slug}\n")
        print(f"Wrote {len(cross_spec)} baseline collision(s) to {args.write_baseline}")
        return 0

    baseline = load_baseline(args.baseline)
    new_collisions = {s: o for s, o in cross_spec.items() if s not in baseline}
    grandfathered = len(cross_spec) - len(new_collisions)

    if within_spec:
        print(f"\n⚠️  {len(within_spec)} within-spec duplicate slug(s) (Mintlify resolves these, but they are ambiguous):")
        for slug, occ in sorted(within_spec.items()):
            print(f"  /api-reference/{slug}")
            for o in occ:
                print(f"      {o['method']:6} {o['path']}  (tag: {o['tag']}, summary: {o['summary']!r})")

    if grandfathered:
        print(f"\nℹ️  {grandfathered} cross-spec collision(s) ignored via baseline ({args.baseline}).")

    report = new_collisions if baseline else cross_spec
    if report:
        kind = "NEW " if baseline else ""
        print(f"\n❌ {len(report)} {kind}cross-spec slug collision(s) — these silently overwrite each other at build time:")
        for slug, occ in sorted(report.items()):
            print(f"\n  /api-reference/{slug}")
            for o in occ:
                print(f"      [{o['spec']}]  {o['method']:6} {o['path']}  (tag: {o['tag']}, summary: {o['summary']!r})")
        print("\nFix: make the tag and/or summary unique per spec in the SOURCE OpenAPI spec")
        print("(e.g. tag the Admin spec's key operations 'Org Keys', or rename summaries like")
        print("'Create an organisation key.'). Tags differing only by case still collide.")
        print("Do NOT edit swagger/*.yml directly in tyk-docs — they are auto-synced and overwritten.")
        if args.warn_only:
            print("\n(--warn-only: not failing the build)")
            return 0
        return 1

    print("\n✅ No cross-spec OpenAPI page-slug collisions found"
          + (" beyond the baseline." if baseline else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
