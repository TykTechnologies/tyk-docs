#!/usr/bin/env python3
"""
Add noindex: true to frontmatter of all MDX files in old version directories.
This script excludes the latest version from getting noindex added.
"""

import json
import re
from pathlib import Path
import frontmatter
import sys

# === CONFIG ===
ROOT_DIR = Path.cwd()
DOCS_JSON_PATH = ROOT_DIR / "docs.json"


def get_latest_version_identifier():
    """Get the latest version identifier from docs.json."""
    if not DOCS_JSON_PATH.exists():
        print(f"❌ docs.json not found at {DOCS_JSON_PATH}")
        sys.exit(1)

    with open(DOCS_JSON_PATH, 'r', encoding='utf-8') as f:
        docs_config = json.load(f)

    versions = docs_config.get("navigation", {}).get("versions", [])
    
    if not versions:
        print("❌ No versions found in docs.json")
        sys.exit(1)

    # First version is the latest
    latest = versions[0]
    version_str = latest.get("version", "")
    
    # Extract version number from string like "v5.11 (latest)" or "v5.10"
    # The latest version typically doesn't have a sourceFolder and content is at root
    match = re.match(r'v?(\d+\.\d+)', version_str)
    if match:
        return match.group(1)  # Return just the numeric part like "5.11"
    
    return None


def get_all_version_folders():
    """Get all version folders (directories that match version pattern like 5.8, 5.9, etc.)."""
    version_folders = []
    
    # Look for directories that match version pattern (e.g., 5.8, 5.9, 5.10, nightly)
    for item in ROOT_DIR.iterdir():
        if item.is_dir():
            # Check if it's a version folder (numeric pattern or 'nightly')
            if re.match(r'^\d+\.\d+$', item.name) or item.name == 'nightly':
                version_folders.append(item.name)
    
    return sorted(version_folders)


def add_noindex_to_file(file_path):
    """Add noindex: "noindex, follow" to the frontmatter of an MDX file."""
    try:
        # Read the file with frontmatter
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Check if noindex already exists with the correct value
        current_noindex = post.get('noindex', False)
        
        # If it's already set to "noindex, follow", skip
        if current_noindex == "noindex, follow":
            return False  # No change needed
        
        # Add noindex: "noindex, follow"
        post['noindex'] = "noindex, follow"
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        return True  # File was modified
        
    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {str(e)}")
        return False


def process_version_folder(version_folder):
    """Process all MDX files in a version folder and add noindex: true."""
    version_path = ROOT_DIR / version_folder
    
    if not version_path.exists():
        print(f"⚠️  Version folder not found: {version_folder}")
        return 0
    
    modified_count = 0
    mdx_files = list(version_path.rglob("*.mdx"))
    
    print(f"📁 Processing {version_folder}/ ({len(mdx_files)} MDX files)...")
    
    for mdx_file in mdx_files:
        if add_noindex_to_file(mdx_file):
            modified_count += 1
    
    return modified_count


def main():
    print("🔍 Adding noindex to old version folders...")
    print("=" * 80)
    
    # Get latest version identifier
    latest_version_num = get_latest_version_identifier()
    
    if not latest_version_num:
        print("⚠️  Could not determine latest version from docs.json")
        print("⚠️  Will add noindex to all version folders")
        latest_version = None
    else:
        latest_version = latest_version_num
        print(f"✅ Latest version: {latest_version}")
        print(f"ℹ️  Latest version content is at root (no version folder)")
    
    print()
    
    # Get all version folders
    all_versions = get_all_version_folders()
    
    if not all_versions:
        print("✅ No version folders found to process. All done!")
        return
    
    print(f"📋 Found {len(all_versions)} version folders: {', '.join(all_versions)}")
    print()
    
    # Filter out the latest version if it has a folder (unlikely but check anyway)
    if latest_version:
        old_versions = [v for v in all_versions if v != latest_version]
    else:
        # If we couldn't determine latest, process all version folders
        old_versions = all_versions
    
    if not old_versions:
        print("✅ No old versions to process. All done!")
        return
    
    print(f"🎯 Will add noindex: true to {len(old_versions)} version folders:")
    print(f"   {', '.join(old_versions)}")
    print()
    
    if latest_version:
        print(f"⏭️  Skipping latest version {latest_version} (content at root, not in folder)")
    
    print()
    print("=" * 80)
    
    # Process each old version
    total_modified = 0
    
    for version in old_versions:
        modified = process_version_folder(version)
        total_modified += modified
        if modified > 0:
            print(f"   ✅ Modified {modified} files in {version}/")
        else:
            print(f"   ⏭️  No changes needed in {version}/")
    
    print()
    print("=" * 80)
    print(f"✅ Complete! Modified {total_modified} files across {len(old_versions)} version folders")
    print(f"🚫 These pages will now be excluded from sitemap.xml")


if __name__ == "__main__":
    main()
