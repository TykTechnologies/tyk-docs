#!/usr/bin/env python3
"""Pin the OSS Gateway quick start to the latest stable Tyk Gateway release on Docker Hub."""

import argparse
import importlib.util
import re
import sys
import urllib.error
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUICK_START = REPO_ROOT / "deployment-and-operations/tyk-open-source-api-gateway/quick-start.mdx"
IMAGE_REPO = "tykio/tyk-gateway"
VERSION = r"\d+\.\d+\.\d+"


def load_updater():
    # Reuse the tyk-install updater's Docker Hub resolver so both jobs agree on "latest".
    sys.dont_write_bytecode = True
    path = Path(__file__).with_name("sync-versions-updater.py")
    spec = importlib.util.spec_from_file_location("sync_versions_updater", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render(text: str, version: str) -> str:
    replacements = [
        (rf"(image: {re.escape(IMAGE_REPO)}:v){VERSION}", rf"\g<1>{version}", "image tag"),
        (rf"^`v{VERSION}` is the latest release\.", f"`v{version}` is the latest release.", "latest note"),
        (rf'("status":"pass","version":"){VERSION}(")', rf"\g<1>{version}\2", "hello output"),
    ]
    for pattern, replacement, label in replacements:
        text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError(f"{QUICK_START.name}: expected 1 replacement for {label}, got {count}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the result without writing files.")
    args = parser.parse_args()

    try:
        tag = load_updater().latest_tag(IMAGE_REPO, allow_prerelease=False)
        version = tag.removeprefix("v")
        original = QUICK_START.read_text()
        updated = render(original, version)
    except (RuntimeError, ValueError, urllib.error.URLError) as exc:
        print(f"Failed to prepare quick start update: {exc}", file=sys.stderr)
        return 1

    print(f"Latest Tyk Gateway release: {tag}")
    if updated == original:
        print("Quick start already pinned to the latest release.")
    elif args.dry_run:
        print(f"Would update {QUICK_START.relative_to(REPO_ROOT)}")
    else:
        QUICK_START.write_text(updated)
        print(f"Updated {QUICK_START.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
