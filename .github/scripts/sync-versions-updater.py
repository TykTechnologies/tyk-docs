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
    "gateway": {
        "repo": "tykio/tyk-gateway",
        "allow_prerelease": False,
    },
    "mdcb": {
        "repo": "tykio/tyk-mdcb-docker",
        "allow_prerelease": False,
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


Replacement = tuple[str, str, str]


# One entry per image the updater pins: the Docker Hub image name, the
# `.env.example` variable that carries its tag, and the `repository:` value the
# Helm values files use. The Helm value defaults to the image name; the OSS
# gateway is the exception because tyk-charts defaults to Tyk's own registry
# (`docker.tyk.io/tyk-gateway/tyk-gateway`), which mirrors the same tags as
# `tykio/tyk-gateway` on Docker Hub, so either spelling is accepted there.
IMAGES = {
    "dashboard": {"image": "tykio/tyk-dashboard", "env": "DASHBOARD_VERSION"},
    "gateway_ee": {"image": "tykio/tyk-gateway-ee", "env": "GATEWAY_VERSION"},
    "gateway": {
        "image": "tykio/tyk-gateway",
        "env": "GATEWAY_VERSION",
        "helm": r"(?:docker\.tyk\.io/tyk-gateway/tyk-gateway|tykio/tyk-gateway)",
    },
    "pump": {"image": "tykio/tyk-pump-docker-pub", "env": "PUMP_VERSION"},
    "portal": {"image": "tykio/portal", "env": "PORTAL_VERSION"},
    "mdcb": {"image": "tykio/tyk-mdcb-docker", "env": "MDCB_VERSION"},
    "ai_studio": {"image": "tykio/tyk-ai-studio", "env": "AI_STUDIO_VERSION"},
    "microgateway": {"image": "tykio/tyk-microgateway", "env": "MICROGATEWAY_VERSION"},
}


def env_pins(versions: dict[str, str], components: list[str]) -> list[Replacement]:
    # `NAME_VERSION=v1.2.3` lines in `.env.example` files and the READMEs that
    # quote them.
    return [
        (rf"^({IMAGES[name]['env']}=).+$", rf"\g<1>{versions[name]}", f"{name} env")
        for name in components
    ]


def compose_fallbacks(versions: dict[str, str], components: list[str]) -> list[Replacement]:
    # `image: tykio/name:${NAME_VERSION:-v1.2.3}` defaults in compose files. The
    # optional `}` before the colon tolerates the `${REGISTRY:-tykio/name}:${...}`
    # form the AI Studio compose uses.
    return [
        (
            rf"({IMAGES[name]['image']}\}}?:\$\{{{IMAGES[name]['env']}:-)[^}}]+(\}})",
            rf"\g<1>{versions[name]}\2",
            f"{name} fallback",
        )
        for name in components
    ]


def helm_tags(versions: dict[str, str], components: list[str]) -> list[Replacement]:
    # `repository: tykio/name` followed by `tag: v1.2.3` in Helm values files.
    return [
        (
            rf"(repository: {IMAGES[name].get('helm', IMAGES[name]['image'])}\s+tag: ){PINNED_VERSION}",
            rf"\g<1>{versions[name]}",
            f"{name} tag",
        )
        for name in components
    ]


def render_file(path: Path, replacements: list[Replacement]) -> str:
    original = path.read_text()
    updated = original
    for pattern, replacement, label in replacements:
        updated = replace_pattern(updated, pattern, replacement, path, label)
    return updated


def render_replacements(replacements: dict[Path, list[Replacement]]) -> dict[Path, str]:
    return {
        path: render_file(path, file_replacements)
        for path, file_replacements in replacements.items()
    }


def build_replacements(versions: dict[str, str]) -> dict[Path, list[Replacement]]:
    self_managed = ["dashboard", "gateway_ee", "pump", "portal"]
    hybrid = ["gateway_ee", "pump"]
    oss = ["gateway", "pump"]
    ai_studio = ["ai_studio", "microgateway"]
    control_plane = ["dashboard", "gateway_ee", "pump", "mdcb"]
    data_plane = ["gateway_ee", "pump"]

    return {
        REPO_ROOT / "docker/self-managed/.env.example": env_pins(versions, self_managed),
        REPO_ROOT / "docker/self-managed/docker-compose.yml": compose_fallbacks(versions, self_managed),
        REPO_ROOT / "docker/self-managed/README.md": (
            env_pins(versions, self_managed) + compose_fallbacks(versions, ["portal"])
        ),
        REPO_ROOT / "docker/hybrid/.env.example": env_pins(versions, hybrid),
        REPO_ROOT / "docker/hybrid/docker-compose.yml": compose_fallbacks(versions, hybrid),
        REPO_ROOT / "docker/hybrid/README.md": env_pins(versions, hybrid),
        REPO_ROOT / "docker/ai-studio/.env.example": env_pins(versions, ai_studio),
        REPO_ROOT / "docker/ai-studio/docker-compose.yml": compose_fallbacks(versions, ai_studio),
        REPO_ROOT / "docker/oss/.env.example": env_pins(versions, oss),
        REPO_ROOT / "docker/oss/docker-compose.yml": compose_fallbacks(versions, oss),
        REPO_ROOT / "docker/mdcb/control-plane/.env.example": env_pins(versions, control_plane),
        REPO_ROOT / "docker/mdcb/control-plane/docker-compose.yml": compose_fallbacks(versions, control_plane),
        REPO_ROOT / "docker/mdcb/data-plane/.env.example": env_pins(versions, data_plane),
        REPO_ROOT / "docker/mdcb/data-plane/docker-compose.yml": compose_fallbacks(versions, data_plane),
        REPO_ROOT / "kubernetes/helm-self-managed/values.yaml": helm_tags(versions, self_managed),
        REPO_ROOT / "kubernetes/helm-hybrid/values.yaml": helm_tags(versions, hybrid),
        REPO_ROOT / "kubernetes/helm-oss/values.yaml": helm_tags(versions, ["gateway"]),
        REPO_ROOT / "kubernetes/helm-mdcb/values-control-plane.yaml": helm_tags(
            versions, ["mdcb", "dashboard", "gateway_ee", "pump"]
        ),
        REPO_ROOT / "kubernetes/helm-mdcb/values-data-plane.yaml": helm_tags(versions, data_plane),
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
        targets = build_replacements(versions)
        # A target that does not exist yet (a deployment path added to
        # tyk-install after this script) is skipped, not an error, so the two
        # repositories can move independently. A target that exists but does
        # not match still fails.
        present, missing = {}, []
        for path, file_replacements in targets.items():
            if path.is_file():
                present[path] = file_replacements
            else:
                missing.append(path)
        rendered_files = render_replacements(present)
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

    if missing:
        print()
        print("Skipped targets that do not exist in this checkout:")
        for path in missing:
            print(f"  {path.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
