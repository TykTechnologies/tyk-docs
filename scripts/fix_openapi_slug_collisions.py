#!/usr/bin/env python3
"""
Automatically resolve Mintlify OpenAPI page-slug collisions (DX-2380).

validate_openapi_slugs.py *detects* two operations sharing the same generated page
slug (<directory>/<slug(tag)>/<slug(summary)>). This script *fixes* every collision it
finds by giving every operation in a colliding group except one an explicit
`x-mint.href` override (a Mintlify OpenAPI extension - see
https://www.mintlify.com/docs/api-playground/openapi-setup) pointing at a unique page
URL, plus `x-mint.metadata.sidebarTitle` set to the operation's own unmodified summary
(without it, Mintlify's sidebar falls back to a titleized version of the href instead
of the summary - confirmed by live-testing tyk-docs#2572/#2573).

Deliberately does NOT touch `summary`, `tags`, or `description` on any operation - the
fix is pure URL plumbing, invisible to a reader browsing the page itself.

Within one colliding group, exactly one operation keeps its default (no override) slug,
so its URL never changes and nothing needs a redirect. "Which one" is decided
deterministically (SPEC_PRIORITY, then path, then method) rather than by whatever
Mintlify's build happens to render first today - a real production ambiguity that this
script has no way to observe. Every other operation gets:

    x-mint:
      href: <directory>/<tag-slug>/<summary-slug>-<spec-dir-name>-<operationId-slug>
      metadata:
        sidebarTitle: <original summary, unchanged>

`operationId` is required to be unique within one OpenAPI document, and combined with
the spec's own directory name (globally unique by construction), the combination can
never collide with anything else - regardless of whether the original collision was
within one spec or across several.

Insertion is done as a targeted text edit anchored on the operation's `operationId:`
line (which must therefore be present and unique in its file), not a full YAML
load/dump, so the rest of each file is untouched byte-for-byte.

Usage:
    python3 scripts/fix_openapi_slug_collisions.py [directory]              # apply fixes
    python3 scripts/fix_openapi_slug_collisions.py [directory] --check      # report only, exit 1 if anything would change
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_openapi_slugs import (  # noqa: E402
    collect_slugs,
    find_openapi_specs,
    openapi_directory_name,
    slugify,
)

# Mirrors OPENAPI_SPEC_DIRECTORY_NAMES's own ordering (validate_openapi_slugs.py /
# merge_docs_configs.py) - Gateway is the most foundational/most-referenced product, so
# it's first and therefore always the one that keeps its default slug when it's part of
# a collision. Order after that follows the same "more specialized loses" convention
# established across the DX-2380 fix PRs.
SPEC_PRIORITY = [
    "gateway-swagger.yml",
    "dashboard-swagger.yml",
    "dashboard-admin-swagger.yml",
    "mdcb-swagger.yml",
    "identity-broker-swagger.yml",
    "enterprise-developer-portal-swagger.yaml",
    "ai-studio-swagger.yml",
]


def spec_priority_key(spec_rel):
    basename = spec_rel.rsplit("/", 1)[-1]
    try:
        return SPEC_PRIORITY.index(basename)
    except ValueError:
        return len(SPEC_PRIORITY)


def slugify_operation_id(operation_id):
    """Camel-case-aware slug so word boundaries survive (addKey -> add-key, not addkey)."""
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", operation_id)
    return slugify(spaced)


def disambiguator_slug(occ):
    """A slug guaranteed unique within one spec: operationId when present (OpenAPI
    requires this to be unique per document), otherwise method+path (also always
    unique per document - you can't declare the same method twice under one path).
    Never a constant placeholder - two operations in the same collision group both
    lacking operationId must still get distinct suffixes from each other."""
    if occ["operation_id"]:
        return slugify_operation_id(occ["operation_id"])
    return slugify(f"{occ['method']}-{occ['path']}")


def plan_fixes(root, docs_json_path):
    """Return list of (occurrence, href, sidebar_title) for every operation that needs
    an x-mint override - i.e. every member of a colliding group except the first."""
    specs = find_openapi_specs(docs_json_path)
    slug_map = collect_slugs(root, specs)

    fixes = []
    for occurrences in slug_map.values():
        if len(occurrences) < 2:
            continue
        ordered = sorted(
            occurrences,
            key=lambda o: (spec_priority_key(o["spec"]), o["path"], o["method"]),
        )
        for occ in ordered[1:]:
            spec_basename = occ["spec"].rsplit("/", 1)[-1]
            spec_dir_name = openapi_directory_name(spec_basename)
            href = (
                f"/{occ['directory']}/{slugify(occ['tag'])}/{slugify(occ['summary'])}"
                f"-{spec_dir_name}-{disambiguator_slug(occ)}"
            )
            fixes.append((occ, href, occ["summary"]))
    return fixes


def find_operation_line(lines, path, method):
    """Locate the line index of `<method>:` nested directly under the `<path>:` key.
    Path keys may or may not be YAML-quoted (varies by generator - e.g. ai-studio's
    swag-generated spec quotes every path, gateway/dashboard's hand-authored ones
    don't), so match either form. Returns the index of the method line itself -
    the x-mint block is inserted as its first child, which is always valid
    regardless of whether the operation has an operationId."""
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
                break  # left the path's block without finding the method
            mm = method_pattern.match(lines[j])
            if mm and stripped_indent == path_indent + 2:
                return j
    return None


def apply_fix(root, occ, href, sidebar_title):
    file_path = os.path.join(root, occ["spec"])
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    idx = find_operation_line(lines, occ["path"], occ["method"])
    if idx is None:
        raise RuntimeError(
            f"{occ['spec']}: couldn't locate {occ['method']} {occ['path']} in the raw text - "
            "can't safely auto-fix, needs manual attention"
        )
    method_indent = len(lines[idx]) - len(lines[idx].lstrip())
    indent = " " * (method_indent + 2)

    insertion = [
        f"{indent}x-mint:\n",
        f"{indent}  href: {href}\n",
        f"{indent}  metadata:\n",
        f"{indent}    sidebarTitle: {sidebar_title}\n",
    ]
    lines[idx + 1 : idx + 1] = insertion

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory", nargs="?", default=".", help="Repo root containing docs.json (default: .)")
    parser.add_argument("--check", action="store_true", help="Report what would change without writing; exit 1 if anything would change")
    args = parser.parse_args()

    docs_json_path = os.path.join(args.directory, "docs.json")
    if not os.path.isfile(docs_json_path):
        print(f"ERROR: docs.json not found in {args.directory}")
        return 2

    fixes = plan_fixes(args.directory, docs_json_path)

    if args.check:
        if not fixes:
            print("✅ No OpenAPI page-slug collisions need fixing.")
            return 0
        print(f"❌ {len(fixes)} operation(s) need an x-mint.href fix - run without --check to apply, then commit the result:")
        for occ, href, _ in fixes:
            print(f"  [{occ['spec']}] {occ['method']} {occ['path']} (operationId: {occ['operation_id']}) -> {href}")
        return 1

    if not fixes:
        print("✅ No OpenAPI page-slug collisions found - nothing to fix.")
        return 0

    for occ, href, sidebar_title in fixes:
        apply_fix(args.directory, occ, href, sidebar_title)
        print(f"Fixed: [{occ['spec']}] {occ['method']} {occ['path']} -> {href}")
    print(f"\n{len(fixes)} operation(s) fixed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
