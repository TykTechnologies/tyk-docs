#!/usr/bin/env python3

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$")
PINNED_VERSION = r"v\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?"
USER_AGENT = "tyk-version-updater/1.0"


COMPONENTS = {
    "dashboard": {
        "repo": "tykio/tyk-dashboard",
        "allow_prerelease": False,
    },
    "gateway_ee": {
        "repo": "tykio/tyk-gateway-ee",
        "allow_prerelease": False,
    },
    "pump": {
        "repo": "tykio/tyk-pump-docker-pub",
        "allow_prerelease": False,
    },
    "portal": {
        "repo": "tykio/portal",
        "allow_prerelease": False,
    },
    "ai_studio": {
        "repo": "tykio/tyk-ai-studio",
        "allow_prerelease": True,
    },
    "microgateway": {
        "repo": "tykio/tyk-microgateway",
        "allow_prerelease": True,
    },
}


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def prerelease_sort_key(prerelease: str) -> tuple:
    parts = []
    for part in prerelease.split("."):
        number_match = re.search(r"\d+", part)
        prefix = part[: number_match.start()] if number_match else part
        number = int(number_match.group()) if number_match else -1
        suffix = part[number_match.end() :] if number_match else ""
        parts.append((prefix, number, suffix))
    return tuple(parts)


def tag_sort_key(tag: str) -> tuple:
    match = VERSION_TAG.match(tag)
    if not match:
        raise ValueError(f"Invalid version tag: {tag}")

    major, minor, patch, prerelease = match.groups()
    base = tuple(int(part) for part in (major, minor, patch))
    if prerelease is None:
        return (*base, 1, ())
    return (*base, 0, prerelease_sort_key(prerelease))


def latest_tag(image_repo: str, allow_prerelease: bool) -> str:
    namespace, repo = image_repo.split("/", 1)
    url = (
        f"https://hub.docker.com/v2/namespaces/{namespace}/repositories/"
        f"{repo}/tags?page_size=100"
    )
    version_tags = []

    # Docker Hub orders tags by last push, so the newest release is always on
    # the first page; scanning further pages would only matter if 100+ tags
    # were pushed after it.
    payload = fetch_json(url)
    for result in payload.get("results", []):
        name = result.get("name", "")
        match = VERSION_TAG.match(name)
        if not match:
            continue
        prerelease = match.group(4)
        if prerelease and not allow_prerelease:
            continue
        if prerelease and not prerelease.startswith("rc"):
            continue
        version_tags.append((tag_sort_key(name), name))

    if not version_tags:
        release_type = "version" if allow_prerelease else "stable version"
        raise RuntimeError(f"No {release_type} tags found for {image_repo}")

    version_tags.sort()
    return version_tags[-1][1]


def replace_pattern(
    text: str,
    pattern: str,
    replacement: str,
    path: Path,
    label: str,
    expected_count: int = 1,
) -> str:
    updated_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != expected_count:
        raise RuntimeError(
            f"{path}: expected {expected_count} replacement(s) for {label}, got {count}"
        )
    return updated_text


def render_file(path: Path, replacements: list[tuple[str, str, str]]) -> str:
    original = path.read_text()
    updated = original
    for pattern, replacement, label in replacements:
        updated = replace_pattern(updated, pattern, replacement, path, label)
    return updated


def render_replacements(
    replacements: dict[Path, list[tuple[str, str, str]]],
) -> dict[Path, str]:
    return {
        path: render_file(path, file_replacements)
        for path, file_replacements in replacements.items()
    }


def build_replacements(versions: dict[str, str]) -> dict[Path, list[tuple[str, str, str]]]:
    return {
        REPO_ROOT / "docker/self-managed/.env.example": [
            (r"^(DASHBOARD_VERSION=).+$", rf"\g<1>{versions['dashboard']}", "dashboard env"),
            (r"^(GATEWAY_VERSION=).+$", rf"\g<1>{versions['gateway_ee']}", "gateway env"),
            (r"^(PUMP_VERSION=).+$", rf"\g<1>{versions['pump']}", "pump env"),
            (r"^(PORTAL_VERSION=).+$", rf"\g<1>{versions['portal']}", "portal env"),
        ],
        REPO_ROOT / "docker/hybrid/.env.example": [
            (r"^(GATEWAY_VERSION=).+$", rf"\g<1>{versions['gateway_ee']}", "gateway env"),
            (r"^(PUMP_VERSION=).+$", rf"\g<1>{versions['pump']}", "pump env"),
        ],
        REPO_ROOT / "docker/self-managed/docker-compose.yml": [
            (
                r"(tykio/tyk-dashboard:\$\{DASHBOARD_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['dashboard']}\2",
                "dashboard fallback",
            ),
            (
                r"(tykio/tyk-gateway-ee:\$\{GATEWAY_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['gateway_ee']}\2",
                "gateway fallback",
            ),
            (
                r"(tykio/tyk-pump-docker-pub:\$\{PUMP_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['pump']}\2",
                "pump fallback",
            ),
            (
                r"(tykio/portal:\$\{PORTAL_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['portal']}\2",
                "portal fallback",
            ),
        ],
        REPO_ROOT / "docker/hybrid/docker-compose.yml": [
            (
                r"(tykio/tyk-gateway-ee:\$\{GATEWAY_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['gateway_ee']}\2",
                "gateway fallback",
            ),
            (
                r"(tykio/tyk-pump-docker-pub:\$\{PUMP_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['pump']}\2",
                "pump fallback",
            ),
        ],
        REPO_ROOT / "docker/self-managed/README.md": [
            (r"^(DASHBOARD_VERSION=).+$", rf"\g<1>{versions['dashboard']}", "dashboard readme"),
            (r"^(GATEWAY_VERSION=).+$", rf"\g<1>{versions['gateway_ee']}", "gateway readme"),
            (r"^(PUMP_VERSION=).+$", rf"\g<1>{versions['pump']}", "pump readme"),
            (r"^(PORTAL_VERSION=).+$", rf"\g<1>{versions['portal']}", "portal readme"),
            (
                r"(tykio/portal:\$\{PORTAL_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['portal']}\2",
                "portal image example",
            ),
        ],
        REPO_ROOT / "docker/hybrid/README.md": [
            (r"^(GATEWAY_VERSION=).+$", rf"\g<1>{versions['gateway_ee']}", "gateway readme"),
            (r"^(PUMP_VERSION=).+$", rf"\g<1>{versions['pump']}", "pump readme"),
        ],
        REPO_ROOT / "docker/ai-studio/.env.example": [
            (r"^(AI_STUDIO_VERSION=).+$", rf"\g<1>{versions['ai_studio']}", "ai studio env"),
            (
                r"^(MICROGATEWAY_VERSION=).+$",
                rf"\g<1>{versions['microgateway']}",
                "microgateway env",
            ),
        ],
        REPO_ROOT / "docker/ai-studio/docker-compose.yml": [
            (
                r"(tykio/tyk-ai-studio:\$\{AI_STUDIO_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['ai_studio']}\2",
                "ai studio fallback",
            ),
            (
                r"(tykio/tyk-microgateway:\$\{MICROGATEWAY_VERSION:-)[^}]+(\})",
                rf"\g<1>{versions['microgateway']}\2",
                "microgateway fallback",
            ),
        ],
        REPO_ROOT / "kubernetes/helm-self-managed/values.yaml": [
            (
                rf"(repository: tykio/tyk-gateway-ee\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['gateway_ee']}",
                "gateway tag",
            ),
            (
                rf"(repository: tykio/tyk-dashboard\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['dashboard']}",
                "dashboard tag",
            ),
            (
                rf"(repository: tykio/tyk-pump-docker-pub\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['pump']}",
                "pump tag",
            ),
            (
                rf"(repository: tykio/portal\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['portal']}",
                "portal tag",
            ),
        ],
        REPO_ROOT / "kubernetes/helm-hybrid/values.yaml": [
            (
                rf"(repository: tykio/tyk-gateway-ee\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['gateway_ee']}",
                "gateway tag",
            ),
            (
                rf"(repository: tykio/tyk-pump-docker-pub\s+tag: ){PINNED_VERSION}",
                rf"\g<1>{versions['pump']}",
                "pump tag",
            ),
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update pinned Tyk component versions across the repo."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved versions without modifying files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        versions = {
            name: latest_tag(component["repo"], component["allow_prerelease"])
            for name, component in COMPONENTS.items()
        }
        replacements = build_replacements(versions)
        rendered_files = render_replacements(replacements)
    except (RuntimeError, urllib.error.URLError) as exc:
        print(f"Failed to prepare version updates: {exc}", file=sys.stderr)
        return 1

    print("Resolved latest Tyk component image tags:")
    for name, component in sorted(COMPONENTS.items()):
        suffix = " (RCs allowed)" if component["allow_prerelease"] else ""
        print(f"  {name}: {versions[name]}{suffix}")

    if args.dry_run:
        print()
        print("Validated replacement targets. No files changed.")
        return 0

    changed_files = []
    for path, rendered in rendered_files.items():
        if rendered != path.read_text():
            path.write_text(rendered)
            changed_files.append(path)

    print()
    if changed_files:
        print("Updated files:")
        for path in changed_files:
            print(f"  {path.relative_to(REPO_ROOT)}")
    else:
        print("No files changed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
