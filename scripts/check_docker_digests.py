#!/usr/bin/env python3
"""Check the pinned `docker pull image:tag@sha256:...` commands in release notes.

Offline: each digest must belong to one image:tag only. A digest shared by two
tags is almost always a copy-paste from an earlier release.

With --verify-registry: each digest must equal the multi-arch image index digest
that Docker Hub serves for the tag today.
"""

import argparse
import glob
import re
import sys
from collections import defaultdict

PULL_RE = re.compile(r"docker pull\s+([a-z0-9][a-z0-9._/-]*):([A-Za-z0-9._-]+)@sha256:([0-9a-fA-F]+)")
DEFAULT_GLOB = "developer-support/release-notes/*.mdx"
MANIFEST_ACCEPT = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])


def find_pulls(paths):
    pulls = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                for m in PULL_RE.finditer(line):
                    image, tag, digest = m.groups()
                    pulls.append({"file": path, "line": lineno, "image": image,
                                  "tag": tag, "digest": "sha256:" + digest.lower()})
    return pulls


def check_format(pulls):
    return [f"{p['file']}:{p['line']}: {p['image']}:{p['tag']} digest is not 64 hex characters"
            for p in pulls if len(p["digest"]) != len("sha256:") + 64]


def check_duplicates(pulls):
    refs_by_digest = defaultdict(set)
    where = defaultdict(list)
    for p in pulls:
        ref = f"{p['image']}:{p['tag']}"
        refs_by_digest[p["digest"]].add(ref)
        where[p["digest"]].append(f"{p['file']}:{p['line']} ({ref})")
    return [f"{digest} is used by more than one image tag: " + ", ".join(where[digest])
            for digest, refs in refs_by_digest.items() if len(refs) > 1]


def registry_digest(session, image, tag):
    """Return the digest Docker Hub serves for image:tag, or None if the tag does not exist."""
    repo = image if "/" in image else f"library/{image}"
    token = session.get(
        "https://auth.docker.io/token",
        params={"service": "registry.docker.io", "scope": f"repository:{repo}:pull"},
        timeout=20,
    ).json()["token"]
    resp = session.head(
        f"https://registry-1.docker.io/v2/{repo}/manifests/{tag}",
        headers={"Authorization": f"Bearer {token}", "Accept": MANIFEST_ACCEPT},
        timeout=20,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.headers["Docker-Content-Digest"]


def check_registry(pulls, session):
    errors, warnings, cache = [], [], {}
    for p in pulls:
        first = p["image"].split("/")[0]
        if "." in first or ":" in first:
            warnings.append(f"{p['file']}:{p['line']}: skipped {p['image']}, only Docker Hub images are verified")
            continue
        ref = (p["image"], p["tag"])
        if ref not in cache:
            try:
                cache[ref] = registry_digest(session, *ref)
            except Exception as e:  # network problems must not block unrelated docs PRs
                cache[ref] = e
        actual = cache[ref]
        if isinstance(actual, Exception):
            warnings.append(f"{p['file']}:{p['line']}: could not query Docker Hub for {p['image']}:{p['tag']}: {actual}")
        elif actual is None:
            errors.append(f"{p['file']}:{p['line']}: tag {p['image']}:{p['tag']} does not exist on Docker Hub")
        elif actual != p["digest"]:
            errors.append(f"{p['file']}:{p['line']}: {p['image']}:{p['tag']} digest is {p['digest']}, "
                          f"but Docker Hub serves {actual}")
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help=f"files to check (default: {DEFAULT_GLOB})")
    parser.add_argument("--verify-registry", action="store_true",
                        help="also compare each digest with the digest on Docker Hub")
    args = parser.parse_args(argv)

    paths = args.files or sorted(glob.glob(DEFAULT_GLOB))
    pulls = find_pulls(paths)
    errors = check_format(pulls) + check_duplicates(pulls)
    warnings = []
    if args.verify_registry:
        import requests
        reg_errors, warnings = check_registry(pulls, requests.Session())
        errors += reg_errors

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    if errors:
        print(f"\n❌ Found {len(errors)} Docker digest problem(s) in {len(pulls)} pinned pull command(s).")
        print("Get the correct digest with: docker buildx imagetools inspect tykio/<image>:<tag>")
        return 1
    print(f"✅ {len(pulls)} pinned docker pull command(s) checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
