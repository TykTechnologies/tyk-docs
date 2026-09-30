#!/usr/bin/env python3
"""Pin the AI Studio Docker and Kubernetes install guides to the latest stable AI Studio release on Docker Hub."""

import argparse
import importlib.util
import re
import sys
import urllib.error
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDES = REPO_ROOT / "ai-management/ai-studio"
STUDIO_IMAGE = "tykio/tyk-ai-studio-ent"
EDGE_IMAGE = "tykio/tyk-microgateway-ent"
TAG = r"v\d+\.\d+\.\d+"

# (file, pattern, expected replacement count, label)
REPLACEMENTS = [
    ("quickstart.mdx", rf"(image: {re.escape(STUDIO_IMAGE)}:){TAG}", 1, "AI Studio image"),
    ("quickstart.mdx", rf"(image: {re.escape(EDGE_IMAGE)}:){TAG}", 1, "Edge Gateway image"),
    ("deployment-k8s.mdx", rf"(repository: {re.escape(STUDIO_IMAGE)}\n\s+tag: ){TAG}", 2, "AI Studio chart tag"),
    ("deployment-k8s.mdx", rf"(repository: {re.escape(EDGE_IMAGE)}\n\s+tag: ){TAG}", 2, "Edge Gateway chart tag"),
]


def load_updater():
    # Reuse the tyk-install updater's Docker Hub resolver so all sync jobs agree on "latest".
    sys.dont_write_bytecode = True
    path = Path(__file__).with_name("sync-versions-updater.py")
    spec = importlib.util.spec_from_file_location("sync_versions_updater", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_tag() -> str:
    updater = load_updater()
    studio = updater.latest_tag(STUDIO_IMAGE, allow_prerelease=False)
    edge = updater.latest_tag(EDGE_IMAGE, allow_prerelease=False)
    # The tag is written into the guides verbatim, so accept only a plain vX.Y.Z.
    if not re.fullmatch(TAG, studio):
        raise RuntimeError(f"Unexpected tag format from Docker Hub: {studio!r}")
    if studio != edge:
        raise RuntimeError(f"{STUDIO_IMAGE} is at {studio} but {EDGE_IMAGE} is at {edge}")
    return studio


def render(files: dict, tag: str) -> dict:
    updated = dict(files)
    for name, pattern, expected, label in REPLACEMENTS:
        updated[name], count = re.subn(pattern, rf"\g<1>{tag}", updated[name])
        if count != expected:
            raise RuntimeError(f"{name}: expected {expected} replacements for {label}, got {count}")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the result without writing files.")
    args = parser.parse_args()

    names = sorted({name for name, *_ in REPLACEMENTS})
    try:
        tag = resolve_tag()
        original = {name: (GUIDES / name).read_text() for name in names}
        updated = render(original, tag)
    except (RuntimeError, ValueError, urllib.error.URLError) as exc:
        print(f"Failed to prepare AI Studio guide update: {exc}", file=sys.stderr)
        return 1

    print(f"Latest AI Studio release: {tag}")
    changed = [name for name in names if updated[name] != original[name]]
    if not changed:
        print("AI Studio guides already pinned to the latest release.")
    for name in changed:
        path = (GUIDES / name).relative_to(REPO_ROOT)
        if args.dry_run:
            print(f"Would update {path}")
        else:
            (GUIDES / name).write_text(updated[name])
            print(f"Updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
