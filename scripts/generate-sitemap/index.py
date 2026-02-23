import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import os
import yaml
import frontmatter
import xml.etree.ElementTree as ET
from xml.dom import minidom

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


def should_index_page(page_path: str) -> bool:
    """Check if a page should be indexed (noindex not set to true in frontmatter)."""
    # Try different file patterns
    patterns = [
        page_path + ".mdx",
        page_path + "/index.mdx",
    ]

    for pattern in patterns:
        file_path = ROOT_DIR / pattern
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Parse frontmatter
                    post = frontmatter.load(f)
                    noindex = post.get('noindex', False)
                    
                    # Check if noindex is True (handles both boolean and string "True")
                    if isinstance(noindex, bool) and noindex:
                        return False
                    if isinstance(noindex, str) and noindex.lower() == 'true':
                        return False
            except Exception as e:
                # If we can't parse frontmatter, assume it should be indexed
                pass
            break

    return True


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
    """Convert text to lowercase slug with only alphanumeric characters, dashes, and underscores."""
    # Convert to lowercase
    text = text.lower()
    
    # Remove trailing periods first
    text = text.rstrip('.')
    
    # Replace spaces with dashes (but keep underscores)
    text = text.replace(" ", "-")
    
    # Keep only alphanumeric characters (a-z, 0-9), dashes, and underscores
    # Remove all special characters (apostrophes, parentheses, periods, etc.)
    cleaned = ""
    for char in text:
        if char.isalnum() or char == '-' or char == '_':
            cleaned += char
    
    # Clean up multiple consecutive dashes (but not underscores)
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
    """Generate the sitemap XML content with proper formatting."""
    excluded_count = 0

    # Remove duplicates while preserving order
    seen = set()
    unique_pages = []
    for page in pages:
        if page not in seen:
            seen.add(page)
            unique_pages.append(page)

    # Create XML structure using ElementTree
    urlset = ET.Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    urlset.set('xmlns:news', 'http://www.google.com/schemas/sitemap-news/0.9')
    urlset.set('xmlns:xhtml', 'http://www.w3.org/1999/xhtml')
    urlset.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
    urlset.set('xmlns:video', 'http://www.google.com/schemas/sitemap-video/1.1')

    for page in unique_pages:
        # Check if page is already a full URL (from API reference)
        if page.startswith("https://"):
            url_text = page
            lastmod = None  # API references don't have file modification times
            should_index = True  # API references are always indexed
        else:
            # Check if page should be indexed (not marked with noindex)
            should_index = should_index_page(page)
            if not should_index:
                excluded_count += 1
                continue
            
            url_text = build_url(page)
            lastmod = get_file_lastmod(page)

        # Create url element
        url_elem = ET.SubElement(urlset, 'url')
        
        # Add loc element
        loc_elem = ET.SubElement(url_elem, 'loc')
        loc_elem.text = url_text
        
        # Add lastmod element if available
        if lastmod:
            lastmod_elem = ET.SubElement(url_elem, 'lastmod')
            lastmod_elem.text = lastmod

    if excluded_count > 0:
        print(f"🚫 Excluded {excluded_count} pages marked with noindex=true")

    # Convert to string and format with minidom
    xml_string = ET.tostring(urlset, encoding='unicode')
    
    # Parse with minidom for pretty printing
    dom = minidom.parseString(xml_string)
    
    # Format with proper indentation (2 spaces)
    formatted_xml = dom.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')
    
    # Clean up extra blank lines that minidom adds
    lines = [line for line in formatted_xml.split('\n') if line.strip()]
    formatted_xml = '\n'.join(lines)
    
    return formatted_xml


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
