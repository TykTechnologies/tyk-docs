#!/usr/bin/env python3
"""Pin the OSS Gateway quick start to the Gateway LTS version in the release notes overview."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OVERVIEW = REPO_ROOT / "developer-support/release-notes/overview.mdx"
QUICK_START = REPO_ROOT / "deployment-and-operations/tyk-open-source-api-gateway/quick-start.mdx"
IMAGE_REPO = "tykio/tyk-gateway"
VERSION = r"\d+\.\d+\.\d+"
USER_AGENT = "tyk-docs-oss-quickstart-sync/1.0"


def gateway_lts() -> str:
    text = OVERVIEW.read_text()
    marker = "export const releaseData = "
    release_data, _ = json.JSONDecoder().raw_decode(text[text.index(marker) + len(marker) :])
    for component in release_data["opensource"]:
        if component["name"] == "Tyk Gateway":
            lts = component.get("lts", "")
            if not re.fullmatch(VERSION, lts):
                raise RuntimeError(f"Invalid Tyk Gateway lts value in {OVERVIEW.name}: {lts!r}")
            return lts
    raise RuntimeError(f"No Tyk Gateway entry in {OVERVIEW.name}")


def require_image_tag(tag: str) -> None:
    namespace, repo = IMAGE_REPO.split("/", 1)
    url = f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repo}/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{IMAGE_REPO}:{tag} not found on Docker Hub (HTTP {exc.code})") from exc


def render(text: str, lts: str) -> str:
    replacements = [
        (rf"(image: {re.escape(IMAGE_REPO)}:v){VERSION}", rf"\g<1>{lts}", "image tag"),
        (rf"^`v{VERSION}` is the current LTS release\.", f"`v{lts}` is the current LTS release.", "LTS note"),
        (rf'("status":"pass","version":"){VERSION}(")', rf"\g<1>{lts}\2", "hello output"),
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
        lts = gateway_lts()
        require_image_tag(f"v{lts}")
        original = QUICK_START.read_text()
        updated = render(original, lts)
    except (RuntimeError, KeyError, ValueError, urllib.error.URLError) as exc:
        print(f"Failed to prepare quick start update: {exc}", file=sys.stderr)
        return 1

    print(f"Tyk Gateway LTS: v{lts}")
    if updated == original:
        print("Quick start already pinned to the LTS version.")
    elif args.dry_run:
        print(f"Would update {QUICK_START.relative_to(REPO_ROOT)}")
    else:
        QUICK_START.write_text(updated)
        print(f"Updated {QUICK_START.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
