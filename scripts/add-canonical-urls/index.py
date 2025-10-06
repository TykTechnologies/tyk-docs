import os
import re
from pathlib import Path

# === CONFIG ===
ROOT_DIR = Path.cwd()
BASE_URL = "https://tyk.io/docs"

def find_mdx_files(directory: Path):
    """Recursively find all .mdx files excluding any folder named 'snippets'."""
    mdx_files = []
    for root, dirs, files in os.walk(directory):
        # Skip any directory named 'snippets'
        dirs[:] = [d for d in dirs if d != "snippets"]

        for file in files:
            if file.endswith(".mdx"):
                full_path = Path(root) / file
                # Skip if any part of path is 'snippets'
                if "snippets" in full_path.parts:
                    print(f"⏩ Skipping file inside snippets: {full_path}")
                    continue
                mdx_files.append(full_path)
    return mdx_files

def build_canonical_url(file_path: Path):
    """Generate canonical URL, handling index.mdx and stripping version folder."""
    relative_path = file_path.relative_to(ROOT_DIR).as_posix()
    clean_path = re.sub(r"\.mdx$", "", relative_path)

    # Remove trailing '/index' if it's an index.mdx
    canonical_path = re.sub(r"/index$", "", clean_path)
    if canonical_path == "index":
        canonical_path = ""  # top-level index

    # Strip version folder if first segment is a number (like 5.8)
    parts = canonical_path.split("/")
    if parts and re.match(r"^\d+(\.\d+)?$", parts[0]):  # e.g., 5 or 5.8
        parts = parts[1:]  # remove version folder
    canonical_path = "/".join(parts)

    canonical_url = f"{BASE_URL}{'/' + canonical_path if canonical_path else ''}"
    return canonical_url

def add_or_update_canonical(file_path: Path):
    """Add or update the canonical field in the MDX frontmatter."""
    content = file_path.read_text(encoding="utf-8")

    # Match frontmatter between --- and ---
    frontmatter_match = re.match(r"^---\n([\s\S]*?)\n---", content)
    if not frontmatter_match:
        print(f"⚠️  No frontmatter found in: {file_path}")
        return

    frontmatter = frontmatter_match.group(1)
    canonical_url = build_canonical_url(file_path)

    # Add or update canonical field
    if re.search(r'^["\']?canonical["\']?\s*:', frontmatter, flags=re.MULTILINE):
        new_frontmatter = re.sub(
            r'^["\']?canonical["\']?\s*:\s*.*$',
            f'canonical: "{canonical_url}"',
            frontmatter,
            flags=re.MULTILINE
        )
        print(f"🔁 Updated canonical in: {file_path}")
    else:
        new_frontmatter = frontmatter + f'\ncanonical: "{canonical_url}"'
        print(f"📝 Added canonical to: {file_path}")

    new_content = re.sub(
        r"^---\n([\s\S]*?)\n---",
        f"---\n{new_frontmatter}\n---",
        content
    )

    file_path.write_text(new_content, encoding="utf-8")

def main():
    print("🔍 Searching for .mdx files...")
    mdx_files = find_mdx_files(ROOT_DIR)
    print(f"📄 Found {len(mdx_files)} eligible .mdx files")

    for file_path in mdx_files:
        add_or_update_canonical(file_path)

if __name__ == "__main__":
    main()
