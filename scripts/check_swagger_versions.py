#!/usr/bin/env python3
"""Check that each swagger file's info.version matches the release notes.

Expected versions come from the Latest Releases data (snippets/release-data.mdx,
or the inline releaseData in developer-support/release-notes/overview.mdx on
older branches). The branch decides which value applies:

- main, and release-X.Y where X.Y is the Gateway `latest` minor: `latest`.
- release-X.Y where X.Y is the Gateway `lts` minor: `lts`.
- Any other branch: skipped.

Use --fix to rewrite stale info.version values in place. Use --print-branches
to list the latest and LTS release branches (CI checks them from main).
"""

import argparse
import json
import os
import re
import subprocess
import sys

DATA_FILES = ["snippets/release-data.mdx", "developer-support/release-notes/overview.mdx"]

# swagger file -> (release notes path suffix, modes it is checked in, autofix).
# autofix=False: content is not synced from a source release tag (AI Studio is
# behind, TIB is hand-written), so a mismatch is a warning and --fix skips it.
SWAGGER_FILES = {
    "swagger/gateway-swagger.yml": ("release-notes/gateway", {"latest", "lts"}, True),
    "swagger/dashboard-swagger.yml": ("release-notes/dashboard", {"latest", "lts"}, True),
    "swagger/dashboard-admin-swagger.yml": ("release-notes/dashboard", {"latest", "lts"}, True),
    "swagger/mdcb-swagger.yml": ("release-notes/mdcb", {"latest"}, True),
    "swagger/enterprise-developer-portal-swagger.yaml": ("release-notes/portal", {"latest"}, True),
    "swagger/ai-studio-swagger.yml": ("release-notes/ai-studio", {"latest"}, False),
    "swagger/identity-broker-swagger.yml": ("release-notes/tib", {"latest"}, False),
}

INFO_VERSION_RE = re.compile(r"^(info:\n(?:[ \t]+.*\n|\n)*?  version:[ \t]*)(.*)$", re.M)


def load_release_data(root):
    for rel in DATA_FILES:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        m = re.search(r"export const releaseData\s*=\s*", text)
        if m:
            obj, _ = json.JSONDecoder().raw_decode(text, m.end())
            return [c for group in obj.values() for c in group]
    raise SystemExit("❌ No releaseData found in " + " or ".join(DATA_FILES))


def component(data, notes_suffix):
    for c in data:
        if c.get("releaseNotesPath", "").endswith(notes_suffix):
            return c
    return None


def minor(version):
    return ".".join(version.split(".")[:2]) if version else None


def current_branch(root):
    for var in ("GITHUB_BASE_REF", "GITHUB_REF_NAME"):
        if os.environ.get(var):
            return os.environ[var]
    out = subprocess.run(["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"],
                         capture_output=True, text=True)
    return out.stdout.strip()


def branch_mode(branch, gateway):
    if branch == "main":
        return "latest"
    m = re.fullmatch(r"release-(\d+\.\d+)", branch or "")
    if not m:
        return None
    if m.group(1) == minor(gateway.get("lts")):
        return "lts"
    if m.group(1) == minor(gateway.get("latest")):
        return "latest"
    return None


def normalize(v):
    return v.strip().strip("'\"").lstrip("v")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--branch", help="branch to check as (default: GITHUB_BASE_REF, GITHUB_REF_NAME, or the git branch)")
    ap.add_argument("--fix", action="store_true", help="rewrite stale info.version values")
    ap.add_argument("--print-branches", action="store_true", help="print the latest and LTS release branches, then exit")
    args = ap.parse_args()

    data = load_release_data(args.root)
    gateway = component(data, "release-notes/gateway")
    if not gateway:
        raise SystemExit("❌ No Tyk Gateway entry in releaseData")

    if args.print_branches:
        minors = dict.fromkeys(minor(gateway.get(k)) for k in ("latest", "lts"))
        print(" ".join(f"release-{m}" for m in minors if m))
        return 0

    branch = args.branch or current_branch(args.root)
    mode = branch_mode(branch, gateway)
    if not mode:
        print(f"⏭️  Branch '{branch}' is not main, the latest release branch "
              f"(release-{minor(gateway.get('latest'))}) or the LTS branch "
              f"(release-{minor(gateway.get('lts'))}). Skipping.")
        return 0
    print(f"🔍 Branch '{branch}': checking swagger versions against `{mode}`")

    errors, warnings = [], []
    for rel, (notes_suffix, modes, autofix) in SWAGGER_FILES.items():
        path = os.path.join(args.root, rel)
        if mode not in modes or not os.path.exists(path):
            continue
        c = component(data, notes_suffix)
        expected = c and c.get(mode)
        if not expected:
            continue
        text = open(path, encoding="utf-8").read()
        m = INFO_VERSION_RE.search(text)
        if not m:
            errors.append(f"{rel}: no info.version found")
            continue
        actual = normalize(m.group(2))
        if actual == expected:
            print(f"  ✅ {rel}: {expected}")
            continue
        if not autofix:
            warnings.append(f"{rel}: info.version is {m.group(2).strip()}, but the {mode} "
                            f"{c['name']} release is {expected}. Check that the content is "
                            f"current, then set the version by hand.")
            continue
        if args.fix:
            text = text[:m.start(2)] + expected + text[m.end(2):]
            open(path, "w", encoding="utf-8").write(text)
            print(f"  🔧 {rel}: {m.group(2).strip()} -> {expected}")
        else:
            errors.append(f"{rel}: info.version is {m.group(2).strip()}, but the {mode} "
                          f"{c['name']} release is {expected}")

    if warnings:
        print("\n⚠️  Not fixed automatically (content not synced from a release tag):")
        for w in warnings:
            print(f"  - {w}")
            if os.environ.get("GITHUB_ACTIONS"):
                print(f"::warning title=Swagger version ({branch})::{w}")
    if errors:
        print("\n❌ Swagger versions do not match the release notes:")
        for e in errors:
            print(f"  - {e}")
        print(f"\nTo fix, run: python scripts/check_swagger_versions.py . --branch {branch} --fix")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
