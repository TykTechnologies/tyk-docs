import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os
import yaml

# === CONFIG ===
ROOT_DIR = Path.cwd()
BASE_URL = "https://tyk.io/docs"
DOCS_JSON_PATH = ROOT_DIR / "docs.json"
SITEMAP_OUTPUT_PATH = ROOT_DIR / "sitemap.xml"


def extract_pages_recursively(pages: List[Any], collected_pages: List[str] = None) -> List[str]:
    """Recursively extract all page strings and OpenAPI paths from the pages structure."""
    if collected_pages is None:
        collected_pages = []

    for page in pages:
        if isinstance(page, str):
            # It's a page reference
            collected_pages.append(page)
        elif isinstance(page, dict):
            # Check for openapi field first
            if "openapi" in page:
                openapi_path = page["openapi"]
                api_urls = extract_apis_from_swagger(openapi_path)
                collected_pages.extend(api_urls)
            
            # Then handle nested pages
            if "pages" in page:
                extract_pages_recursively(page["pages"], collected_pages)

    return collected_pages


def extract_all_pages_from_version(version: Dict[str, Any]) -> List[str]:
    """Extract all pages from a version's tabs and groups, including OpenAPI endpoints."""
    all_pages = []

    if "tabs" in version:
        for tab in version["tabs"]:
            if "groups" in tab:
                for group in tab["groups"]:
                    # Check for openapi field at group level
                    if "openapi" in group:
                        openapi_path = group["openapi"]
                        api_urls = extract_apis_from_swagger(openapi_path)
                        all_pages.extend(api_urls)
                    
                    # Extract pages recursively (which now also handles openapi in nested pages)
                    if "pages" in group:
                        pages = extract_pages_recursively(group["pages"])
                        all_pages.extend(pages)

    return all_pages


def build_url(page_path: str) -> str:
    """Build the canonical URL for a page path."""
    # Remove .mdx extension if present
    clean_path = re.sub(r"\.mdx$", "", page_path)

    # Handle index pages
    if clean_path.endswith("/index"):
        clean_path = clean_path[:-6]  # Remove '/index'
    elif clean_path == "index":
        clean_path = ""

    # Build the URL
    if clean_path:
        return f"{BASE_URL}/{clean_path}"
    else:
        return BASE_URL


def get_file_lastmod(page_path: str) -> str:
    """Get the last modification time of the file if it exists."""
    # Try different file patterns
    patterns = [
        page_path + ".mdx",
        page_path + "/index.mdx",
    ]

    for pattern in patterns:
        file_path = ROOT_DIR / pattern
        if file_path.exists():
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt.isoformat() + "Z"

    return None


def slugify(text: str) -> str:
    """Convert text to lowercase slug with only alphanumeric characters and dashes."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove trailing periods first
    text = text.rstrip('.')
    
    # Replace spaces and common separators with dashes
    text = text.replace(" ", "-")
    text = text.replace("_", "-")
    
    # Keep only alphanumeric characters (a-z, 0-9) and dashes
    # Remove all special characters (apostrophes, parentheses, periods, etc.)
    cleaned = ""
    for char in text:
        if char.isalnum() or char == '-':
            cleaned += char
    
    # Clean up multiple consecutive dashes
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    
    # Strip leading and trailing dashes
    cleaned = cleaned.strip("-")
    
    return cleaned


def extract_apis_from_swagger(swagger_file_path: str) -> List[str]:
    """Extract API URLs from an OpenAPI/Swagger file."""
    api_urls = []
    
    full_path = ROOT_DIR / swagger_file_path
    
    if not full_path.exists():
        print(f"⚠️  Swagger file not found: {swagger_file_path}")
        return api_urls
    
    try:
        # Load YAML file (supports both .yml and .yaml)
        with open(full_path, "r", encoding="utf-8") as f:
            swagger_content = yaml.safe_load(f)
        
        if not swagger_content:
            print(f"⚠️  Swagger file is empty: {swagger_file_path}")
            return api_urls
        
        # Extract paths from the swagger
        paths = swagger_content.get("paths", {})
        
        if not paths:
            print(f"⚠️  No paths found in swagger file: {swagger_file_path}")
            return api_urls
        
        # Iterate through each path and its operations
        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            
            # Each method (get, post, put, delete, etc.)
            for method, operation in methods.items():
                if method.startswith("x-") or not isinstance(operation, dict):
                    continue
                
                # Extract tag and summary
                tags = operation.get("tags", [])
                summary = operation.get("summary", "")
                
                # We take the first tag if there are multiple
                if tags and summary:
                    tag = tags[0]
                    tag_slug = slugify(tag)
                    summary_slug = slugify(summary)
                    
                    api_url = f"{BASE_URL}/api-reference/{tag_slug}/{summary_slug}"
                    api_urls.append(api_url)
        
        print(f"✅ Extracted {len(api_urls)} APIs from {swagger_file_path}")
        return api_urls
    
    except Exception as e:
        print(f"❌ Error parsing swagger file {swagger_file_path}: {str(e)}")
        return api_urls


def generate_sitemap_xml(pages: List[str]) -> str:
    """Generate the sitemap XML content."""
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    urlset_open = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n'
    urlset_close = '</urlset>'

    url_entries = []

    # Remove duplicates while preserving order
    seen = set()
    unique_pages = []
    for page in pages:
        if page not in seen:
            seen.add(page)
            unique_pages.append(page)

    for page in unique_pages:
        # Check if page is already a full URL (from API reference)
        if page.startswith("https://"):
            url = page
            lastmod = None  # API references don't have file modification times
        else:
            url = build_url(page)
            lastmod = get_file_lastmod(page)

        url_entry = f'<url>\n<loc>{url}</loc>\n'

        if lastmod:
            url_entry += f'<lastmod>{lastmod}</lastmod>\n'

        url_entry += '</url>\n'
        url_entries.append(url_entry)

    sitemap_content = (
        xml_header
        + urlset_open
        + "".join(url_entries)
        + urlset_close
    )

    return sitemap_content


def main():
    print("🔍 Reading docs.json...")

    # Check if docs.json exists
    if not DOCS_JSON_PATH.exists():
        print(f"❌ docs.json not found at {DOCS_JSON_PATH}")
        exit(1)

    # Load docs.json
    with open(DOCS_JSON_PATH, "r", encoding="utf-8") as f:
        docs_config = json.load(f)

    # Get the latest version (first one in the array)
    versions = docs_config.get("navigation", {}).get("versions", [])

    if not versions:
        print("❌ No versions found in docs.json")
        exit(1)

    latest_version = versions[0]
    print(f"📦 Using latest version: {latest_version.get('version', 'Unknown')}")

    # Extract all pages from the latest version
    print("📄 Extracting pages from latest version...")
    pages = extract_all_pages_from_version(latest_version)
    print(f"✅ Found {len(pages)} pages (including duplicates)")

    # Generate sitemap XML
    print("🗂️  Generating sitemap XML...")
    sitemap_xml = generate_sitemap_xml(pages)

    # Write sitemap to file
    print(f"💾 Writing sitemap to {SITEMAP_OUTPUT_PATH}...")
    with open(SITEMAP_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)

    print(f"✅ Sitemap generated successfully!")
    print(f"📊 Sitemap contains {len(set(pages))} unique URLs")
    print(f"📁 Output: {SITEMAP_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
