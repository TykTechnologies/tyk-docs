from __future__ import annotations

import os
import re
import sys
import json
from pathlib import Path

# === CONFIG ===
ROOT_DIR = Path.cwd()
BASE_URL = "https://tyk.io/docs"
MAX_REDIRECT_HOPS = 10


def find_mdx_files(directory: Path):
    """Recursively find all .mdx files excluding any folder named 'snippets'."""
    mdx_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != "snippets"]
        for file in files:
            if file.endswith(".mdx"):
                full_path = Path(root) / file
                if "snippets" in full_path.parts:
                    print(f"⏩ Skipping file inside snippets: {full_path}")
                    continue
                mdx_files.append(full_path)
    return mdx_files


def load_docs_json() -> dict:
    docs_path = ROOT_DIR / "docs.json"
    if not docs_path.exists():
        print(f"❌ docs.json not found at {docs_path}. Run this script from the repo root.")
        sys.exit(1)
    return json.loads(docs_path.read_text(encoding="utf-8"))


def extract_all_nav_pages(obj, pages: set):
    """Recursively collect every string path from the navigation tree."""
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                pages.add(item.strip("/"))
            else:
                extract_all_nav_pages(item, pages)
    elif isinstance(obj, dict):
        for key in ("pages", "tabs", "groups", "versions"):
            if key in obj:
                extract_all_nav_pages(obj[key], pages)


def build_root_nav(docs: dict) -> set:
    """Return nav pages that belong to the latest (root) version — no version prefix."""
    all_pages: set = set()
    extract_all_nav_pages(docs.get("navigation", {}), all_pages)
    return {p for p in all_pages if not re.match(r'^\d+(\.\d+)?/', p) and not p.startswith("nightly/")}


def build_redirect_map(docs: dict) -> dict:
    """Build a flat source -> destination map from docs.json redirects."""
    rmap: dict = {}
    for rule in docs.get("redirects", []):
        src = rule.get("source", "").strip("/").removeprefix("docs/")
        dst = rule.get("destination", "").strip("/").removeprefix("docs/")
        if src and dst:
            rmap[src] = dst
    return rmap


def page_exists_at_root(path: str) -> bool:
    """Check whether a path corresponds to an MDX file in the root (current version)."""
    return (ROOT_DIR / f"{path}.mdx").exists() or (ROOT_DIR / path / "index.mdx").exists()


def resolve_canonical(stripped_path: str, root_nav: set, redirect_map: dict) -> str | None:
    """
    Resolve a version-stripped page path to a canonical URL.

    Resolution order per hop:
      1. Path is in the latest nav tree → valid, return URL.
      2. Path exists as a root-level MDX file (unlisted/hidden page) → valid, return URL.
      3. Path has a redirect entry → follow to destination and repeat.
      4. None of the above → unresolvable, return None.

    The empty path (from a versioned index.mdx) maps to the site root.
    """
    if not stripped_path:
        return BASE_URL  # versioned index page → site root is always valid

    current = stripped_path.strip("/")
    visited: set = set()
    for _ in range(MAX_REDIRECT_HOPS):
        if current in visited:
            return None  # redirect loop
        visited.add(current)
        if current in root_nav or page_exists_at_root(current):
            return f"{BASE_URL}/{current}"
        if current in redirect_map:
            current = redirect_map[current].strip("/")
        else:
            return None
    return None  # exceeded max hops


def add_or_update_canonical(
    file_path: Path,
    root_nav: set,
    redirect_map: dict,
    invalid_paths: list,
):
    """Add or update the canonical field in the MDX frontmatter."""
    content = file_path.read_text(encoding="utf-8")

    frontmatter_match = re.match(r"^---\n([\s\S]*?)\n---", content)
    if not frontmatter_match:
        print(f"⚠️  No frontmatter found in: {file_path}")
        return

    frontmatter = frontmatter_match.group(1)

    # Derive the path segment used for canonical resolution
    relative_path = file_path.relative_to(ROOT_DIR).as_posix()
    clean_path = re.sub(r"\.mdx$", "", relative_path)
    canonical_path = re.sub(r"/index$", "", clean_path)
    if canonical_path == "index":
        canonical_path = ""

    parts = canonical_path.split("/")
    is_versioned = bool(parts and (re.match(r"^\d+(\.\d+)?$", parts[0]) or parts[0] == "nightly"))

    if is_versioned:
        stripped_path = "/".join(parts[1:])
        canonical_url = resolve_canonical(stripped_path, root_nav, redirect_map)
        if canonical_url is None:
            invalid_paths.append((str(file_path.relative_to(ROOT_DIR)), stripped_path))
            return  # leave file unchanged; CI will report and block
    else:
        # Root-level (current version) file — always valid
        canonical_url = f"{BASE_URL}{'/' + canonical_path if canonical_path else ''}"

    # Write canonical into frontmatter
    if re.search(r'^["\']?canonical["\']?\s*:', frontmatter, flags=re.MULTILINE):
        new_frontmatter = re.sub(
            r'^["\']?canonical["\']?\s*:\s*.*$',
            f'canonical: "{canonical_url}"',
            frontmatter,
            flags=re.MULTILINE,
        )
        print(f"🔁 Updated canonical in: {file_path}")
    else:
        new_frontmatter = frontmatter + f'\ncanonical: "{canonical_url}"'
        print(f"📝 Added canonical to: {file_path}")

    new_content = re.sub(
        r"^---\n([\s\S]*?)\n---",
        f"---\n{new_frontmatter}\n---",
        content,
    )
    file_path.write_text(new_content, encoding="utf-8")


def main():
    print("📖 Loading docs.json...")
    docs = load_docs_json()
    root_nav = build_root_nav(docs)
    redirect_map = build_redirect_map(docs)
    print(f"  {len(root_nav)} root nav pages, {len(redirect_map)} redirect rules loaded")

    print("🔍 Searching for .mdx files...")
    mdx_files = find_mdx_files(ROOT_DIR)
    print(f"📄 Found {len(mdx_files)} eligible .mdx files")

    invalid_paths: list = []
    for file_path in mdx_files:
        add_or_update_canonical(file_path, root_nav, redirect_map, invalid_paths)

    if invalid_paths:
        print(f"\n❌ {len(invalid_paths)} versioned page(s) could not be resolved to a valid canonical:")
        print("   (not present in the latest nav tree and no matching redirect in docs.json)\n")
        for file_path, stripped_path in invalid_paths:
            print(f"  file:  {file_path}")
            print(f"  path:  {stripped_path}")
            print()
        print("Fix: add a redirect in docs.json for each path above, then re-run this script.")
        sys.exit(1)

    print("\n✅ All canonicals resolved successfully.")


if __name__ == "__main__":
    main()
