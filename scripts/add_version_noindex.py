from __future__ import annotations

import os
import re
import sys
import json
from pathlib import Path

# === CONFIG ===
ROOT_DIR = Path.cwd()


def load_branches_config() -> dict:
    config_path = ROOT_DIR / "branches-config.json"
    if not config_path.exists():
        print(f"❌ branches-config.json not found at {config_path}. Run this script from the repo root.")
        sys.exit(1)
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_lts_target_folders(config: dict) -> set:
    """Target folders (as they appear in the merged tree) flagged isLts in branches-config.json."""
    lts_folders = set()
    for version_info in config.get("versions", []):
        if version_info.get("isExternal", False):
            continue
        if version_info.get("isLts", False):
            target_folder = version_info.get("targetFolder", version_info.get("folder", ""))
            if target_folder:
                lts_folders.add(target_folder)
    return lts_folders


def find_mdx_files(directory: Path):
    """Recursively find all .mdx files excluding any folder named 'snippets'."""
    mdx_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d != "snippets"]
        for file in files:
            if file.endswith(".mdx"):
                full_path = Path(root) / file
                if "snippets" in full_path.parts:
                    continue
                mdx_files.append(full_path)
    return mdx_files


def version_segment(file_path: Path):
    """Return the version folder name if this file lives under a versioned
    folder (e.g. '5.14', 'nightly'), or None if it's a current-version (root) page."""
    relative_path = file_path.relative_to(ROOT_DIR).as_posix()
    first_segment = relative_path.split("/", 1)[0]
    if re.match(r"^\d+(\.\d+)?$", first_segment) or first_segment == "nightly":
        return first_segment
    return None


def add_noindex_if_missing(file_path: Path) -> str:
    """Add 'noindex: true' plus 'robots: "noindex, follow"' to frontmatter if
    neither field already exists. Both are needed: noindex: true is what
    actually excludes the page from Mintlify's sitemap.xml (confirmed live -
    robots: alone does not, per the long-standing Classic Portal pages, which
    are NOT excluded from /docs/sitemap.xml despite having robots: "noindex,
    nofollow" set); robots: "noindex, follow" is what controls the rendered
    meta tag content, and takes precedence over whatever noindex: true would
    render on its own (confirmed live via tyk-docs#3036 - the combination
    renders exactly "noindex, follow", not "noindex, nofollow").
    Returns one of: 'added', 'skipped-has-robots-or-noindex', 'skipped-no-frontmatter'."""
    content = file_path.read_text(encoding="utf-8")

    frontmatter_match = re.match(r"^---\n([\s\S]*?)\n---", content)
    if not frontmatter_match:
        print(f"⚠️  No frontmatter found in: {file_path}")
        return "skipped-no-frontmatter"

    frontmatter = frontmatter_match.group(1)

    if re.search(r'^["\']?(robots|noindex)["\']?\s*:', frontmatter, flags=re.MULTILINE):
        # A robots or noindex directive already exists (such as a deliberate
        # classic-portal noindex,nofollow) - don't override a page-level
        # content decision.
        return "skipped-has-robots-or-noindex"

    new_frontmatter = frontmatter + '\nnoindex: true\nrobots: "noindex, follow"'
    new_content = re.sub(
        r"^---\n([\s\S]*?)\n---",
        f"---\n{new_frontmatter}\n---",
        content,
    )
    file_path.write_text(new_content, encoding="utf-8")
    print(f"📝 Added noindex to: {file_path}")
    return "added"


def main():
    print("📖 Loading branches-config.json...")
    config = load_branches_config()
    lts_folders = get_lts_target_folders(config)
    print(f"🛡️  LTS versions (kept indexed): {sorted(lts_folders) or 'none'}")

    print("🔍 Searching for .mdx files...")
    mdx_files = find_mdx_files(ROOT_DIR)
    print(f"📄 Found {len(mdx_files)} eligible .mdx files")

    counts = {"added": 0, "skipped-has-robots-or-noindex": 0, "skipped-no-frontmatter": 0, "skipped-current-or-lts": 0}

    for file_path in mdx_files:
        version = version_segment(file_path)
        if version is None or version in lts_folders:
            counts["skipped-current-or-lts"] += 1
            continue
        result = add_noindex_if_missing(file_path)
        counts[result] += 1

    print("\n✅ Version noindex pass complete.")
    print(f"   Added: {counts['added']}")
    print(f"   Already had a robots or noindex directive: {counts['skipped-has-robots-or-noindex']}")
    print(f"   Current version or LTS (untouched): {counts['skipped-current-or-lts']}")
    print(f"   No frontmatter found: {counts['skipped-no-frontmatter']}")


if __name__ == "__main__":
    main()
