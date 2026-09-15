#!/usr/bin/env python3
"""
Noindex non-current, non-LTS OpenAPI-generated API reference pages, and point
their canonical at the current version's equivalent operation (P4).

add_version_noindex.py does this for regular .mdx pages, but Mintlify's
OpenAPI-generated pages (declared via an "openapi" key in docs.json, one page
per operation, no .mdx file backing them) are invisible to that script - and
to add-canonical-urls/index.py. Confirmed live (tyk-docs#3036/#3037) that the
same fix works here too, via Mintlify's x-mint.metadata OpenAPI extension:

    x-mint:
      metadata:
        canonical: "<current version's real URL for this operation>"
        noindex: true
        robots: "noindex, follow"

All three fields are required together, same as the .mdx case: noindex: true
is what actually excludes the page from /docs/sitemap.xml (robots: alone does
not - confirmed via the long-standing Classic Portal pages); robots: "noindex,
follow" is what controls the rendered meta tag content and takes precedence
over whatever noindex: true would render alone (confirmed live - the
combination renders exactly "noindex, follow", preserving link equity).

Cross-version matching is by operationId (must be unique within one OpenAPI
document) plus the spec's own basename (gateway-swagger.yml, etc.), so a
lookup key of (basename, operationId) is safe across specs. If an operation
doesn't exist in the current version's equivalent spec (removed/renamed since),
canonical is left alone (self-canonical is the correct fallback) but noindex
is still applied.

Reuses find_openapi_specs/collect_slugs from validate_openapi_slugs.py so the
resolved current-version URL correctly accounts for any existing x-mint.href
override from fix_openapi_slug_collisions.py (DX-2380) - the current version's
"real" URL for an operation is not always its default <directory>/<tag>/
<summary> slug.

Insertion is a targeted text edit anchored on the operation's `<method>:` line,
not a full YAML load/dump, so the rest of each file (including any existing
x-mint.href/metadata.sidebarTitle from the collision fixer) is preserved
byte-for-byte. Must run AFTER fix_openapi_slug_collisions.py and its
verification step, so every x-mint.href this script might need to merge
alongside already exists and slugs are known collision-free.

Usage:
    python3 scripts/add_openapi_version_noindex.py [directory]   # default: .
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_openapi_slugs import collect_slugs, find_openapi_specs  # noqa: E402

BASE_URL = "https://tyk.io/docs"


def load_branches_config(root: Path) -> dict:
    config_path = root / "branches-config.json"
    if not config_path.exists():
        print(f"❌ branches-config.json not found at {config_path}. Run this script from the repo root.")
        sys.exit(1)
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_latest_and_lts(config: dict):
    """Return (latest target_folder, set of LTS target_folders) from branches-config.json."""
    latest = None
    lts_folders = set()
    for version_info in config.get("versions", []):
        if version_info.get("isExternal", False):
            continue
        target_folder = version_info.get("targetFolder", version_info.get("folder", ""))
        if not target_folder:
            continue
        if version_info.get("isLatest", False):
            latest = target_folder
        if version_info.get("isLts", False):
            lts_folders.add(target_folder)
    return latest, lts_folders


def spec_version(source: str):
    """Extract the version folder from a swagger source path, e.g.
    'swagger/5.14/gateway-swagger.yml' -> '5.14'. None if not version-prefixed."""
    parts = source.split("/")
    if len(parts) >= 3 and parts[0] == "swagger":
        return parts[1]
    return None


def match_key(occ):
    """operationId when present (must be unique within one OpenAPI document),
    otherwise (method, path) - mirrors fix_openapi_slug_collisions.py's own
    disambiguator_slug fallback. Several specs here (AI Studio, Enterprise
    Developer Portal) don't set operationId on most operations, so relying on
    operationId alone would leave most of their pages unmatched."""
    if occ["operation_id"]:
        return ("id", occ["operation_id"])
    return ("path", occ["method"], occ["path"])


def build_current_slug_lookup(slug_map, latest_version):
    """Map (spec_basename, match_key) -> full_slug, for every operation
    belonging to the current (isLatest) version's specs."""
    lookup = {}
    for full_slug, occurrences in slug_map.items():
        for occ in occurrences:
            if spec_version(occ["spec"]) != latest_version:
                continue
            basename = occ["spec"].rsplit("/", 1)[-1]
            lookup[(basename, match_key(occ))] = full_slug
    return lookup


def find_operation_line(lines, path, method):
    """Same approach as fix_openapi_slug_collisions.py: locate the line index
    of `<method>:` nested directly under the `<path>:` key, tolerating
    YAML-quoted or unquoted path keys."""
    import re

    path_pattern = re.compile(r'^(\s*)"?' + re.escape(path) + r'"?:\s*$')
    for i, line in enumerate(lines):
        m = path_pattern.match(line)
        if not m:
            continue
        path_indent = len(m.group(1))
        method_pattern = re.compile(r"^(\s*)" + re.escape(method.lower()) + r":\s*$")
        for j in range(i + 1, len(lines)):
            stripped_indent = len(lines[j]) - len(lines[j].lstrip())
            if lines[j].strip() and stripped_indent <= path_indent:
                break
            mm = method_pattern.match(lines[j])
            if mm and stripped_indent == path_indent + 2:
                return j
    return None


def block_end(lines, start, indent):
    """Index of the first line after `start` whose indent is <= `indent`
    (i.e. the line one past the end of the block that starts at `start`,
    whose children are indented deeper than `indent`). Blank lines don't
    count as block boundaries."""
    for k in range(start, len(lines)):
        if not lines[k].strip():
            continue
        stripped_indent = len(lines[k]) - len(lines[k].lstrip())
        if stripped_indent <= indent:
            return k
    return len(lines)


def apply_fix(file_path: Path, path: str, method: str, canonical_url):
    """Insert or merge x-mint.metadata.{canonical,noindex,robots} for one
    operation. Returns True if the file was changed."""
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

    idx = find_operation_line(lines, path, method)
    if idx is None:
        print(f"  ⚠️  Couldn't locate {method} {path} in {file_path} - skipping")
        return False

    method_indent = len(lines[idx]) - len(lines[idx].lstrip())
    xmint_indent = method_indent + 2
    field_indent = method_indent + 4
    metadata_child_indent = method_indent + 6

    new_fields = []
    if canonical_url:
        new_fields.append(f'{" " * metadata_child_indent}canonical: "{canonical_url}"\n')
    new_fields.append(f'{" " * metadata_child_indent}noindex: true\n')
    new_fields.append(f'{" " * metadata_child_indent}robots: "noindex, follow"\n')

    next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
    has_xmint = next_line.strip() == "x-mint:" and (len(next_line) - len(next_line.lstrip())) == xmint_indent

    if not has_xmint:
        # No existing x-mint block at all - insert a brand new one.
        insertion = [f'{" " * xmint_indent}x-mint:\n', f'{" " * field_indent}metadata:\n'] + new_fields
        lines[idx + 1 : idx + 1] = insertion
        file_path.write_text("".join(lines), encoding="utf-8")
        return True

    # x-mint exists (from fix_openapi_slug_collisions.py, or a manual override).
    xmint_end = block_end(lines, idx + 2, xmint_indent)
    metadata_idx = None
    for k in range(idx + 2, xmint_end):
        stripped = lines[k].strip()
        line_indent = len(lines[k]) - len(lines[k].lstrip())
        if stripped == "metadata:" and line_indent == field_indent:
            metadata_idx = k
            break

    if metadata_idx is None:
        # x-mint exists (e.g. href only) but has no metadata block yet - add one
        # as the last child of x-mint.
        insertion = [f'{" " * field_indent}metadata:\n'] + new_fields
        lines[xmint_end:xmint_end] = insertion
    else:
        # metadata: already exists (e.g. sidebarTitle from the collision fixer) -
        # append our fields as additional children, after its existing ones.
        metadata_end = block_end(lines, metadata_idx + 1, field_indent)
        # Don't duplicate a field this operation may already carry (e.g. a
        # manually-set canonical/noindex/robots) - leave those alone entirely.
        existing_keys = set()
        for k in range(metadata_idx + 1, metadata_end):
            stripped = lines[k].strip()
            if ":" in stripped:
                existing_keys.add(stripped.split(":", 1)[0].strip())
        filtered_fields = [
            f for f in new_fields
            if f.strip().split(":", 1)[0].strip() not in existing_keys
        ]
        if not filtered_fields:
            return False
        lines[metadata_end:metadata_end] = filtered_fields

    file_path.write_text("".join(lines), encoding="utf-8")
    return True


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    docs_json_path = root / "docs.json"
    if not docs_json_path.is_file():
        print(f"❌ docs.json not found in {root}")
        return 2

    config = load_branches_config(root)
    latest_version, lts_folders = get_latest_and_lts(config)
    print(f"⭐ Current version: {latest_version}")
    print(f"🛡️  LTS versions (kept indexed): {sorted(lts_folders) or 'none'}")

    print("📖 Reading OpenAPI specs from docs.json...")
    specs = find_openapi_specs(str(docs_json_path))
    slug_map = collect_slugs(str(root), specs)
    current_lookup = build_current_slug_lookup(slug_map, latest_version)
    print(f"📄 {len(specs)} spec(s), {sum(len(v) for v in slug_map.values())} operation(s) total, "
          f"{len(current_lookup)} in the current version")

    counts = {"canonical+noindex": 0, "noindex-only": 0, "skipped-current-or-lts": 0, "skipped-unchanged": 0}

    for full_slug, occurrences in slug_map.items():
        for occ in occurrences:
            version = spec_version(occ["spec"])
            if version is None or version == latest_version or version in lts_folders:
                counts["skipped-current-or-lts"] += 1
                continue

            basename = occ["spec"].rsplit("/", 1)[-1]
            current_slug = current_lookup.get((basename, match_key(occ)))
            canonical_url = f"{BASE_URL}/{current_slug}" if current_slug else None

            file_path = root / occ["spec"]
            changed = apply_fix(file_path, occ["path"], occ["method"], canonical_url)
            if changed:
                counts["canonical+noindex" if canonical_url else "noindex-only"] += 1
            else:
                counts["skipped-unchanged"] += 1

    print("\n✅ OpenAPI version noindex pass complete.")
    print(f"   Canonical + noindex added: {counts['canonical+noindex']}")
    print(f"   Noindex only (no current-version match found): {counts['noindex-only']}")
    print(f"   Current version or LTS (untouched): {counts['skipped-current-or-lts']}")
    print(f"   Already had these fields (untouched): {counts['skipped-unchanged']}")


if __name__ == "__main__":
    main()
