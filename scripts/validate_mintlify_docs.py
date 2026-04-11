#!/usr/bin/env python3
"""
Script to check for broken links in converted Mintlify documentation.


WHAT THIS SCRIPT VALIDATES:

1. BROKEN LINKS & IMAGES:
   - Scans all MDX files for internal links and verifies they exist
   - Checks image references and verifies image files exist
   - Handles various file patterns (.mdx extensions, index files, etc.)
   - Considers redirects when checking link existence

2. DOCS.JSON VALIDATION (--validate-redirects flag):
   - Self-referencing redirects (source = destination)
   - Navigation-redirect conflicts (same path in both navigation and redirects)
   - Invalid redirects (empty source or destination)
   - Missing navigation files (navigation entries pointing to non-existent files)
   - Missing redirect destinations (redirect destinations pointing to non-existent files)

3. ANCHOR VALIDATION (--check-anchors flag):
   - Scans all internal links that contain fragment identifiers (e.g. /page#section)
   - Resolves the target file and extracts all valid anchors from it:
     * GFM-slugified headings (Mintlify's default anchor format)
     * Custom heading IDs via {#id} syntax
     * HTML <a id="..."> and <a name="..."> elements
   - Reports links whose anchor does not exist in the target file

4. EXTERNAL LINK VALIDATION (--external-links flag):
   - Checks all external HTTP/HTTPS URLs return a non-4xx/5xx response
   - Uses HEAD requests with a GET fallback
   - Configurable timeout and per-request delay for rate limiting

USAGE:
   python validate_mintlify_docs.py [directory] [options]
   make check-redirects    # Validate redirects and navigation only
   make validate-all       # Full validation with verbose output
   python scripts/validate_mintlify_docs.py . --external-links --external-timeout 5 --external-delay 0.5
   python scripts/validate_mintlify_docs.py . --check-anchors
"""

import os
import re
import glob
import json
import argparse
import urllib.parse
import requests
import time
from pathlib import Path
from typing import Optional, Set, List, Tuple, Dict, Any

def remove_comments_and_code(content: str) -> str:
    """Remove JSX comments, HTML comments, and code blocks from content."""
    # Remove JSX comments: {/* ... */} (including multi-line)
    jsx_comment_pattern = r'\{/\*.*?\*/\}'
    content = re.sub(jsx_comment_pattern, '', content, flags=re.DOTALL)
    
    # Remove HTML comments: <!-- ... --> (including multi-line)
    html_comment_pattern = r'<!--.*?-->'
    content = re.sub(html_comment_pattern, '', content, flags=re.DOTALL)
    
    # Remove fenced code blocks: ``` ... ``` (including multi-line)
    fenced_code_pattern = r'```.*?```'
    content = re.sub(fenced_code_pattern, '', content, flags=re.DOTALL)
    
    # Remove inline code: ` ... `
    inline_code_pattern = r'`[^`\n]*`'
    content = re.sub(inline_code_pattern, '', content)
    
    return content

def slugify_heading(text: str) -> str:
    """Convert a heading string to a Mintlify-compatible anchor slug.

    Mintlify's heading-to-anchor algorithm (empirically determined):
      1. Strip leading/trailing whitespace and lowercase
      2. Remove inline HTML tags and markdown formatting (* _ ` ~)
      3. Remove grouping/separator chars () [] / ? ! : entirely — preserves surrounding spaces
         e.g. "(mTLS)" -> "mTLS", "A / B" -> "A  B" (double space -> double hyphen)
         "Step 1: Create" -> "Step 1 Create" -> "step-1-create" (colon omitted, not "-")
      4. Convert remaining non-alphanumeric, non-space, non-hyphen chars to '-'
         e.g. "5.1.1" -> "5-1-1", "." -> "-"
      5. Replace each individual space with a hyphen (NO collapsing of runs)
         e.g. "A  B" (double space) -> "A--B" (double hyphen)
      6. Strip leading hyphens only (keep trailing — e.g. "Heading ?" -> "heading-")
    """
    slug = text.strip().lower()
    # Remove inline HTML tags (e.g. <code>, <strong>)
    slug = re.sub(r'<[^>]+>', '', slug)
    # Remove markdown formatting characters (* _ ` ~)
    slug = re.sub(r'[*_`~]', '', slug)
    # Remove grouping/separator chars entirely (keep surrounding spaces intact so
    # "A / B" -> "A  B" -> "A--B" rather than "A - B" -> "A---B")
    # Colon is also omitted by Mintlify: "Step 1: Create" -> "step-1-create" (not "--")
    slug = re.sub(r'[()[\]/?!:]', '', slug)
    # Convert remaining non-alphanumeric, non-space, non-hyphen chars to hyphen
    # (handles . , ; & @ # etc.)
    slug = re.sub(r'[^\w\s-]', '-', slug)
    # Replace each individual space with a hyphen (no run-collapsing so that
    # double spaces — left by removed chars — produce double hyphens)
    slug = slug.replace(' ', '-')
    # Strip leading hyphens only (keep trailing — they are meaningful in Mintlify)
    return slug.lstrip('-')


def extract_file_anchors(content: str) -> Set[str]:
    """Return all valid anchor IDs defined within an MDX file.

    Sources considered:
    - ATX headings (## Heading) → GFM slug, with Mintlify-style duplicate
      disambiguation: the second occurrence of a slug gets a '-1' suffix,
      the third gets '-2', etc.
    - Custom heading IDs: ## Heading {#custom-id} → custom-id (overrides slug,
      no disambiguation applied)
    - HTML <a id="..."> and <a name="..."> elements
    """
    anchors: Set[str] = set()
    # Track how many times each base slug has appeared for disambiguation
    slug_count: Dict[str, int] = {}

    heading_re = re.compile(
        r'^(?:\d+\.\s+|[-*+]\s+)?#{1,6}\s+(.+?)(?:\s+\{#([^}]+)\})?\s*$',
        re.MULTILINE,
    )
    for m in heading_re.finditer(content):
        custom_id = m.group(2)
        if custom_id:
            anchors.add(custom_id.strip())
        else:
            slug = slugify_heading(m.group(1))
            if not slug:
                continue
            count = slug_count.get(slug, 0)
            slug_count[slug] = count + 1
            anchors.add(slug)
            if count > 0:
                # Mintlify disambiguates: 2nd occurrence → slug-1, 3rd → slug-2 …
                anchors.add(f"{slug}-{count}")

    # <a id="..."> and <a name="...">
    for attr in ('id', 'name'):
        for m in re.finditer(
            rf'<a[^>]+{attr}=["\']([^"\']+)["\']', content, re.IGNORECASE
        ):
            anchors.add(m.group(1))

    return anchors


def build_anchor_map(directory: str) -> Dict[str, Set[str]]:
    """Build a mapping of normalised file path → set of anchors for every MDX file."""
    anchor_map: Dict[str, Set[str]] = {}
    for mdx_file in glob.glob(os.path.join(directory, '**/*.mdx'), recursive=True):
        try:
            with open(mdx_file, encoding='utf-8') as fh:
                content = fh.read()
            rel = os.path.relpath(mdx_file, directory)
            anchor_map[rel] = extract_file_anchors(content)
        except Exception as e:
            print(f"Warning: could not read {mdx_file} for anchor extraction: {e}")
    return anchor_map


def find_internal_links_with_anchors(mdx_content: str) -> Set[Tuple[str, str]]:
    """Extract internal links that contain an anchor fragment.

    Returns a set of (normalised_path, anchor) tuples.  Only links that have
    a non-empty fragment are included; links without fragments are handled by
    the existing find_internal_links() function.
    """
    clean = remove_comments_and_code(mdx_content)
    results: Set[Tuple[str, str]] = set()

    patterns = [
        r'\[[^\]]*\]\(([^)]+)\)',           # [text](url)
        r'<a[^>]+href=["\']([^"\']+)["\']', # <a href="url">
        r'<Card[^>]+href=["\']([^"\']+)["\']',  # <Card href="url">
    ]

    for pattern in patterns:
        for m in re.finditer(pattern, clean, re.IGNORECASE):
            raw = m.group(1).strip().strip('"\'')

            # Skip external URLs and pure-anchor links
            if raw.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://', '#', '<mailto:')):
                continue

            if '#' not in raw:
                continue

            path_part, anchor = raw.split('#', 1)
            if not anchor:
                continue

            # Normalise the path the same way find_internal_links does
            path_part = path_part.split('?')[0]  # strip query params
            if path_part.startswith('/'):
                path_part = path_part[1:]
            path_part = path_part.rstrip('/')

            if path_part:  # skip anchor-only refs on the current page
                results.add((path_part, anchor))

    return results


def resolve_file_path(
    path: str,
    existing_files: Set[str],
    redirects: Dict[str, str],
) -> Optional[str]:
    """Resolve a normalised link path to a relative file path (with .mdx extension).

    Returns the relative path (e.g. 'api-management/rate-limit.mdx') or None
    if the file cannot be found even after following redirects.
    """
    candidates = [
        f"{path}.mdx",
        path,
        f"{path}/index.mdx",
        f"{path}/index",
    ]
    for c in candidates:
        if c in existing_files:
            # Return with .mdx extension if it's a known file
            return c if c.endswith('.mdx') else f"{c}.mdx"

    # Try redirect
    for key in (path, f"/{path}"):
        if key in redirects:
            dest = redirects[key].lstrip('/')
            if dest != path:
                return resolve_file_path(dest, existing_files, redirects)

    return None


def check_broken_anchors(
    base_dir: str,
    file_anchor_links: Dict[str, Set[Tuple[str, str]]],
    anchor_map: Dict[str, Set[str]],
    existing_files: Set[str],
    redirects: Dict[str, str],
    anchor_target_excludes: List[str],
) -> Dict[str, List[Tuple[str, str]]]:
    """Check that every anchor fragment in internal links resolves in the target file.

    Returns a dict mapping source file → list of (link_with_anchor, reason) tuples.
    anchor_target_excludes: list of relative file paths (with or without .mdx) whose
    anchors should not be validated (e.g. files that pull content via MDX imports).
    """
    # Normalise excludes to bare paths without extension for comparison
    excluded = {p.removesuffix('.mdx') for p in anchor_target_excludes}

    broken: Dict[str, List[Tuple[str, str]]] = {}

    for source_file, links in file_anchor_links.items():
        file_broken: List[Tuple[str, str]] = []
        for path, anchor in sorted(links):
            # Skip if the target file is in the exclude list
            if path.removesuffix('.mdx') in excluded:
                continue

            rel_file = resolve_file_path(path, existing_files, redirects)

            if rel_file is None:
                # File itself doesn't exist — already caught by broken-link check
                continue

            file_anchors = anchor_map.get(rel_file, set())
            if anchor not in file_anchors:
                file_broken.append((f"{path}#{anchor}", f"anchor '#{anchor}' not found in {rel_file}"))

        if file_broken:
            broken[source_file] = file_broken

    return broken


def find_internal_links(mdx_content: str) -> Set[str]:
    """Extract all internal links from MDX content, excluding links in comments and code blocks."""
    # Remove comments and code blocks first to avoid parsing commented-out or code example links
    clean_content = remove_comments_and_code(mdx_content)
    
    internal_links = set()
    
    # Pattern for markdown links: [text](path) - exclude external URLs
    markdown_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
    
    # Pattern for HTML anchor tags: <a href="path">
    html_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
    
    # Pattern for Card components: <Card href="path" ...>
    card_pattern = r'<Card[^>]+href=["\']([^"\']+)["\']'
    
    # Find all matches
    for pattern in [markdown_pattern, html_pattern, card_pattern]:
        matches = re.findall(pattern, clean_content, re.IGNORECASE)
        for match in matches:
            # For markdown pattern, match[1] is the URL, for HTML/Card patterns, match is the URL
            url = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            
            # Skip external URLs, anchors, and special protocols (including malformed mailto)
            if (not url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')) and
                not url.startswith('#') and
                not url.startswith('<mailto:') and  # Skip malformed mailto links
                url.strip()):
                # Clean up the path
                clean_url = url.strip().strip('"\'')
                
                # Skip external URLs after cleaning (handles spaces before URLs)
                if clean_url.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
                    continue
                
                # Remove URL fragments (anchors)
                if '#' in clean_url:
                    clean_url = clean_url.split('#')[0]
                # Remove query parameters
                if '?' in clean_url:
                    clean_url = clean_url.split('?')[0]
                # Remove leading slash if present (normalize paths)
                if clean_url.startswith('/'):
                    clean_url = clean_url[1:]
                # Remove trailing slash if present (normalize paths)
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                if clean_url:  # Only add non-empty paths
                    internal_links.add(clean_url)
    
    return internal_links

def find_image_references(mdx_content: str) -> Set[str]:
    """Extract all image references from MDX content, excluding images in comments and code blocks."""
    # Remove comments and code blocks first to avoid parsing commented-out or code example images
    clean_content = remove_comments_and_code(mdx_content)
    
    image_refs = set()
    
    # Pattern for markdown images: ![alt](path)
    markdown_pattern = r'!\[.*?\]\(([^)]+)\)'
    
    # Pattern for HTML img tags: <img src="path" ...>
    html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
    
    # Pattern for JSX img elements: <img src={"/path"} or <img src="/path"
    jsx_pattern = r'<img[^>]+src=\{?["\']([^"\']+)["\']'
    
    # Pattern for Card components: <Card img="path" ...>
    card_pattern = r'<Card[^>]+img=["\']([^"\']+)["\']'
    
    # Find all matches
    for pattern in [markdown_pattern, html_pattern, jsx_pattern, card_pattern]:
        matches = re.findall(pattern, clean_content, re.IGNORECASE)
        for match in matches:
            # Skip external URLs
            if not match.startswith(('http://', 'https://', 'data:')):
                # Clean up the path
                clean_path = match.strip().strip('"\'')
                # Remove leading slash if present (normalize paths)
                if clean_path.startswith('/'):
                    clean_path = clean_path[1:]
                image_refs.add(clean_path)
    
    return image_refs

def find_external_links(mdx_content: str) -> Set[str]:
    """Extract all external HTTP/HTTPS links from MDX content, excluding links in comments and code blocks."""
    # Remove comments and code blocks first to avoid parsing commented-out or code example links
    clean_content = remove_comments_and_code(mdx_content)
    
    external_links = set()
    
    # Pattern for markdown links: [text](https://...)
    markdown_pattern = r'\[([^\]]*)\]\((https?://[^)]+)\)'
    
    # Pattern for HTML anchor tags: <a href="https://...">
    html_pattern = r'<a[^>]+href=["\']?(https?://[^"\'>\s]+)["\']?'
    
    # Pattern for Card components: <Card href="https://..." ...>
    card_pattern = r'<Card[^>]+href=["\']?(https?://[^"\'>\s]+)["\']?'
    
    # Find all matches
    for pattern in [markdown_pattern, html_pattern, card_pattern]:
        matches = re.findall(pattern, clean_content, re.IGNORECASE)
        for match in matches:
            # For markdown pattern, match[1] is the URL, for HTML/Card patterns, match is the URL
            url = match[1] if isinstance(match, tuple) and len(match) > 1 else match
            
            # Clean up the URL
            clean_url = url.strip().strip('"\'')
            if clean_url:
                external_links.add(clean_url)
    
    return external_links

def scan_mdx_files(directory: str, check_external: bool = False, check_anchors: bool = False) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[Tuple[str, str]]]]:
    """Scan all MDX files and return links, images, external links, and anchor links by file."""
    file_links: Dict[str, Set[str]] = {}
    file_images: Dict[str, Set[str]] = {}
    file_external_links: Dict[str, Set[str]] = {}
    file_anchor_links: Dict[str, Set[Tuple[str, str]]] = {}
    mdx_files = glob.glob(os.path.join(directory, '**/*.mdx'), recursive=True)

    print(f"Scanning {len(mdx_files)} MDX files for links and images...")

    for mdx_file in mdx_files:
        try:
            with open(mdx_file, 'r', encoding='utf-8') as f:
                content = f.read()

            rel_path = os.path.relpath(mdx_file, directory)

            links = find_internal_links(content)
            images = find_image_references(content)

            if links:
                file_links[rel_path] = links
            if images:
                file_images[rel_path] = images

            if check_external:
                external_links = find_external_links(content)
                if external_links:
                    file_external_links[rel_path] = external_links

            if check_anchors:
                anchor_links = find_internal_links_with_anchors(content)
                if anchor_links:
                    file_anchor_links[rel_path] = anchor_links

        except Exception as e:
            print(f"Error reading {mdx_file}: {e}")

    return file_links, file_images, file_external_links, file_anchor_links

def load_redirects(directory: str) -> Dict[str, str]:
    """Load redirects from docs.json or mint.json configuration files."""
    redirects = {}
    
    # Look for configuration files
    config_files = ['docs.json', 'mint.json']
    
    for config_file in config_files:
        config_path = os.path.join(directory, config_file)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Extract redirects if they exist
                if 'redirects' in config:
                    for redirect in config['redirects']:
                        if 'source' in redirect and 'destination' in redirect:
                            source = redirect['source'].strip('/')
                            destination = redirect['destination'].strip('/')
                            redirects[source] = destination
                            
                print(f"Loaded {len(redirects)} redirects from {config_file}")
                break  # Use first config file found
                        
            except Exception as e:
                print(f"Error reading {config_file}: {e}")
    
    return redirects

def find_existing_files(directory: str) -> Set[str]:
    """Find all existing files in the directory."""
    existing_files = set()
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Get relative path from the base directory
            rel_path = os.path.relpath(os.path.join(root, file), directory)
            existing_files.add(rel_path)
            
            # Also add without extension for MDX files (common linking pattern)
            if file.endswith('.mdx'):
                rel_path_no_ext = rel_path[:-4]  # Remove .mdx
                existing_files.add(rel_path_no_ext)
    
    return existing_files

def check_link_exists(link: str, existing_files: Set[str], redirects: Dict[str, str]) -> bool:
    """Check if a link exists, considering redirects and various file patterns."""
    
    # Check exact match
    if link in existing_files:
        return True
    
    # Check with .mdx extension
    if f"{link}.mdx" in existing_files:
        return True
    
    # Check if it's a directory with index file
    if f"{link}/index.mdx" in existing_files:
        return True
    
    if f"{link}/index" in existing_files:
        return True
    
    # Check if there's a redirect for this link
    if link in redirects:
        destination = redirects[link]
        # Recursively check if the redirect destination exists
        return check_link_exists(destination, existing_files, redirects)
    
    # Check if link with leading slash has a redirect
    if f"/{link}" in redirects:
        destination = redirects[f"/{link}"]
        return check_link_exists(destination.lstrip('/'), existing_files, redirects)
    
    return False

def check_external_link(url: str, timeout: int = 10) -> Dict[str, Any]:
    """Check if an external URL is accessible."""
    try:
        # Use HEAD request for faster checking
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Mintlify-Link-Checker/1.0)'
        }
        response = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        
        return {
            'url': url,
            'status_code': response.status_code,
            'accessible': response.status_code < 400,
            'final_url': response.url if response.url != url else None,
            'error': None,
            'response_time': None
        }
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'status_code': None,
            'accessible': False,
            'final_url': None,
            'error': f'Timeout after {timeout}s',
            'response_time': None
        }
    except requests.exceptions.ConnectionError:
        return {
            'url': url,
            'status_code': None,
            'accessible': False,
            'final_url': None,
            'error': 'Connection refused',
            'response_time': None
        }
    except Exception as e:
        return {
            'url': url,
            'status_code': None,
            'accessible': False,
            'final_url': None,
            'error': str(e),
            'response_time': None
        }

def check_external_links(file_external_links: Dict[str, Set[str]], timeout: int = 10, delay: float = 1.0) -> Dict[str, List[Dict[str, Any]]]:
    """Check all external links and return results by file."""
    # Collect all unique URLs to avoid duplicate checking
    all_urls = set()
    for urls in file_external_links.values():
        all_urls.update(urls)
    
    if not all_urls:
        return {}
    
    print(f"\n🔍 Checking {len(all_urls)} unique external URLs...")
    
    # Check each unique URL
    url_results = {}
    for i, url in enumerate(sorted(all_urls), 1):
        print(f"  [{i}/{len(all_urls)}] {url[:60]}{'...' if len(url) > 60 else ''}", end=' ')
        
        start_time = time.time()
        result = check_external_link(url, timeout)
        result['response_time'] = time.time() - start_time
        
        # Print status
        if result['accessible']:
            if result['final_url']:
                print(f"🔄 {result['status_code']} → {result['final_url'][:40]}{'...' if len(result['final_url']) > 40 else ''}")
            else:
                print(f"✅ {result['status_code']}")
        else:
            if result['error']:
                print(f"❌ {result['error']}")
            else:
                print(f"❌ {result['status_code']}")
        
        url_results[url] = result
        
        # Rate limiting
        if i < len(all_urls):
            time.sleep(delay)
    
    # Map results back to files
    file_results = {}
    for file_path, urls in file_external_links.items():
        file_results[file_path] = [url_results[url] for url in urls]
    
    return file_results

def check_broken_links(
    base_dir: str,
    check_external: bool = False,
    external_timeout: int = 10,
    external_delay: float = 1.0,
    check_anchors: bool = False,
    anchor_target_excludes: Optional[List[str]] = None,
) -> Tuple[
    Dict[str, List[str]],
    Dict[str, List[str]],
    Dict[str, str],
    Dict[str, List[Dict[str, Any]]],
    Dict[str, List[Tuple[str, str]]],
]:
    """Check for broken internal links, missing images, and optionally external links and anchors."""
    print(f"Checking for broken links in: {base_dir}")

    redirects = load_redirects(base_dir)
    file_links, file_images, file_external_links, file_anchor_links = scan_mdx_files(
        base_dir, check_external, check_anchors
    )
    existing_files = find_existing_files(base_dir)

    broken_links: Dict[str, List[str]] = {}
    broken_images: Dict[str, List[str]] = {}

    for file_path, links in file_links.items():
        file_broken = [l for l in links if not check_link_exists(l, existing_files, redirects)]
        if file_broken:
            broken_links[file_path] = file_broken

    for file_path, images in file_images.items():
        file_broken = [img for img in images if img not in existing_files]
        if file_broken:
            broken_images[file_path] = file_broken

    external_results: Dict[str, List[Dict[str, Any]]] = {}
    if check_external and file_external_links:
        external_results = check_external_links(file_external_links, external_timeout, external_delay)

    broken_anchor_results: Dict[str, List[Tuple[str, str]]] = {}
    if check_anchors and file_anchor_links:
        print(f"\n🔍 Building anchor map for {base_dir}...")
        anchor_map = build_anchor_map(base_dir)
        broken_anchor_results = check_broken_anchors(
            base_dir, file_anchor_links, anchor_map, existing_files, redirects,
            anchor_target_excludes=anchor_target_excludes or [],
        )

    return broken_links, broken_images, redirects, external_results, broken_anchor_results


def extract_navigation_links(navigation: Dict[str, Any]) -> Set[str]:
    """Extract all navigation links from the navigation structure."""
    links = set()
    
    def process_item(item):
        if isinstance(item, str):
            # Direct page reference
            links.add(item)
        elif isinstance(item, dict):
            if 'pages' in item:
                # Group with pages
                for page in item['pages']:
                    process_item(page)
            elif 'groups' in item:
                # Tab with groups
                for group in item['groups']:
                    process_item(group)
    
    # Process tabs
    if 'tabs' in navigation:
        for tab in navigation['tabs']:
            if 'pages' in tab:
                for page in tab['pages']:
                    process_item(page)
            if 'groups' in tab:
                for group in tab['groups']:
                    process_item(group)
    
    return links


def validate_navigation_files(directory: str, navigation: Dict[str, Any]) -> List[str]:
    """Check if all navigation entries point to existing files."""
    missing_files = []
    existing_files = find_existing_files(directory)
    redirects = load_redirects(directory)
    
    nav_links = extract_navigation_links(navigation)
    
    for link in nav_links:
        # Clean the link path (remove leading slash if present)
        clean_link = link.lstrip('/')
        
        # Check if the navigation file exists using the same logic as broken link checking
        if not check_link_exists(clean_link, existing_files, redirects):
            missing_files.append(link)
    
    return missing_files


def validate_redirect_destinations(directory: str, redirects_list: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Check if all redirect destinations point to existing files."""
    missing_destinations = []
    existing_files = find_existing_files(directory)
    redirects_dict = load_redirects(directory)
    
    for redirect in redirects_list:
        source = redirect.get('source', '')
        destination = redirect.get('destination', '')
        
        if not destination:
            continue  # Skip invalid redirects (handled elsewhere)
        
        # Skip external URLs
        if destination.startswith(('http://', 'https://', 'mailto:', 'tel:', 'ftp://')):
            continue
        
        # Skip anchor-only links
        if destination.startswith('#'):
            continue
        
        # Clean the destination path (remove leading slash if present)
        clean_destination = destination.lstrip('/')
        
        # Remove anchor fragments from destination for file existence check
        if '#' in clean_destination:
            clean_destination = clean_destination.split('#')[0]
        
        # Remove query parameters from destination for file existence check
        if '?' in clean_destination:
            clean_destination = clean_destination.split('?')[0]
        
        # Skip empty destinations after cleaning
        if not clean_destination:
            continue
        
        # Check if the redirect destination exists using the same logic as broken link checking
        if not check_link_exists(clean_destination, existing_files, redirects_dict):
            missing_destinations.append({
                'source': source,
                'destination': destination,
                'clean_destination': clean_destination
            })
    
    return missing_destinations


def validate_docs_json(directory: str) -> Dict[str, Any]:
    """Validate docs.json for problematic redirects and navigation conflicts."""
    docs_json_path = os.path.join(directory, 'docs.json')
    
    if not os.path.exists(docs_json_path):
        return {
            'error': f'docs.json not found in {directory}',
            'self_referencing_redirects': [],
            'navigation_redirect_conflicts': [],
            'invalid_redirects': [],
            'missing_navigation_files': []
        }
    
    try:
        with open(docs_json_path, 'r', encoding='utf-8') as f:
            docs_config = json.load(f)
    except Exception as e:
        return {
            'error': f'Error reading docs.json: {e}',
            'self_referencing_redirects': [],
            'navigation_redirect_conflicts': [],
            'invalid_redirects': [],
            'missing_navigation_files': []
        }
    
    # Extract navigation and redirects
    navigation = docs_config.get('navigation', {})
    redirects = docs_config.get('redirects', [])
    
    # Find self-referencing redirects
    self_referencing = []
    invalid_redirects = []
    
    for redirect in redirects:
        source = redirect.get('source', '')
        destination = redirect.get('destination', '')
        
        # Check for self-referencing redirects
        if source == destination:
            self_referencing.append(redirect)
        
        # Check for invalid redirects (empty source or destination)
        if not source or not destination:
            invalid_redirects.append(redirect)
    
    # Find navigation-redirect conflicts
    nav_links = extract_navigation_links(navigation)
    nav_paths = set()
    
    # Convert nav links to paths with leading slash
    for link in nav_links:
        if not link.startswith('/'):
            nav_paths.add('/' + link)
        else:
            nav_paths.add(link)
    
    # Find conflicts
    conflicts = []
    for redirect in redirects:
        source = redirect.get('source', '')
        if source in nav_paths:
            conflicts.append({
                'source': source,
                'destination': redirect.get('destination', ''),
                'redirect': redirect
            })
    
    # Check for missing navigation files
    missing_nav_files = validate_navigation_files(directory, navigation)
    
    # Check for missing redirect destinations
    missing_redirect_destinations = validate_redirect_destinations(directory, redirects)
    
    return {
        'total_redirects': len(redirects),
        'total_navigation_links': len(nav_links),
        'self_referencing_redirects': self_referencing,
        'navigation_redirect_conflicts': conflicts,
        'invalid_redirects': invalid_redirects,
        'missing_navigation_files': missing_nav_files,
        'missing_redirect_destinations': missing_redirect_destinations
    }


def main():
    parser = argparse.ArgumentParser(description='Check for broken links in converted documentation')
    parser.add_argument('directory', nargs='?', default='converted', help='Directory to scan (default: converted)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--images-only', action='store_true', help='Only check for broken images')
    parser.add_argument('--links-only', action='store_true', help='Only check for broken links')
    parser.add_argument('--validate-redirects', action='store_true', help='Validate docs.json for problematic redirects')
    parser.add_argument('--external-links', action='store_true', help='Check external HTTP/HTTPS links')
    parser.add_argument('--external-timeout', type=int, default=10, help='Timeout for external link requests (default: 10s)')
    parser.add_argument('--external-delay', type=float, default=1.0, help='Delay between external link requests (default: 1.0s)')
    parser.add_argument('--external-only', action='store_true', help='Only check external links')
    parser.add_argument('--external-errors-only', action='store_true', help='Only show failed external links')
    parser.add_argument('--check-anchors', action='store_true', help='Validate anchor fragments in internal links')
    parser.add_argument('--anchor-target-excludes', nargs='*', default=[], metavar='PATH',
                        help='Relative file paths whose anchors should not be validated (e.g. auto-generated files that use MDX imports)')

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        return 1

    # Check for broken links and images
    broken_links, broken_images, redirects, external_results, broken_anchors = check_broken_links(
        args.directory,
        check_external=args.external_links or args.external_only,
        external_timeout=args.external_timeout,
        external_delay=args.external_delay,
        check_anchors=args.check_anchors,
        anchor_target_excludes=args.anchor_target_excludes,
    )
    
    # Validate docs.json if requested
    validation_results = None
    if args.validate_redirects:
        validation_results = validate_docs_json(args.directory)
    
    # Report results
    print(f"\n{'='*60}")
    print("BROKEN LINK ANALYSIS RESULTS")
    print(f"{'='*60}")
    
    total_broken_links = sum(len(links) for links in broken_links.values())
    total_broken_images = sum(len(images) for images in broken_images.values())
    
    if not args.images_only and not args.external_only and broken_links:
        print(f"\n🔗 BROKEN INTERNAL LINKS ({total_broken_links} total):")
        for file_path, links in sorted(broken_links.items()):
            print(f"\n  📄 {file_path}:")
            for link in sorted(links):
                print(f"    ❌ {link}")
    
    if not args.links_only and not args.external_only and broken_images:
        print(f"\n🖼️  BROKEN IMAGE REFERENCES ({total_broken_images} total):")
        for file_path, images in sorted(broken_images.items()):
            print(f"\n  📄 {file_path}:")
            for image in sorted(images):
                print(f"    ❌ {image}")
    
    # Report external link results
    if external_results:
        # Count results
        total_external = sum(len(results) for results in external_results.values())
        successful_external = sum(1 for results in external_results.values() for result in results if result['accessible'])
        failed_external = total_external - successful_external
        redirected_external = sum(1 for results in external_results.values() for result in results if result['final_url'])
        
        if args.external_errors_only:
            # Show only failed external links
            print(f"\n🌐 FAILED EXTERNAL LINKS ({failed_external} total):")
            for file_path, results in sorted(external_results.items()):
                failed_results = [r for r in results if not r['accessible']]
                if failed_results:
                    print(f"\n  📄 {file_path}:")
                    for result in failed_results:
                        if result['error']:
                            print(f"    ❌ {result['url']} ({result['error']})")
                        else:
                            print(f"    ❌ {result['url']} ({result['status_code']})")
        else:
            # Show all external link results
            print(f"\n🌐 EXTERNAL LINK VALIDATION RESULTS ({total_external} total):")
            for file_path, results in sorted(external_results.items()):
                print(f"\n  📄 {file_path}:")
                for result in results:
                    if result['accessible']:
                        if result['final_url']:
                            print(f"    🔄 {result['url']} ({result['status_code']} → {result['final_url']})")
                        else:
                            print(f"    ✅ {result['url']} ({result['status_code']})")
                    else:
                        if result['error']:
                            print(f"    ❌ {result['url']} ({result['error']})")
                        else:
                            print(f"    ❌ {result['url']} ({result['status_code']})")
        
        # Show external link summary
        print(f"\n📊 EXTERNAL LINK SUMMARY:")
        print(f"   ✅ Successful (2xx): {successful_external} links")
        print(f"   🔄 Redirects (3xx): {redirected_external} links")
        print(f"   ❌ Failed: {failed_external} links")
    
    # Report broken anchor results
    if broken_anchors:
        total_broken_anchors = sum(len(v) for v in broken_anchors.values())
        print(f"\n⚓ BROKEN ANCHOR FRAGMENTS ({total_broken_anchors} total):")
        for file_path, issues in sorted(broken_anchors.items()):
            print(f"\n  📄 {file_path}:")
            for link, reason in sorted(issues):
                print(f"    ❌ {link}  ({reason})")

    # Report validation results
    if validation_results:
        print(f"\n{'='*60}")
        print("DOCS.JSON VALIDATION RESULTS")
        print(f"{'='*60}")
        
        if 'error' in validation_results:
            print(f"❌ {validation_results['error']}")
        else:
            print(f"📊 Total redirects: {validation_results['total_redirects']}")
            print(f"📊 Total navigation links: {validation_results['total_navigation_links']}")
            
            # Self-referencing redirects
            self_ref = validation_results['self_referencing_redirects']
            if self_ref:
                print(f"\n⚠️  SELF-REFERENCING REDIRECTS ({len(self_ref)} found):")
                for redirect in self_ref:
                    print(f"    ❌ {redirect['source']} → {redirect['destination']}")
            else:
                print("\n✅ No self-referencing redirects found!")
            
            # Navigation-redirect conflicts
            conflicts = validation_results['navigation_redirect_conflicts']
            if conflicts:
                print(f"\n⚠️  NAVIGATION-REDIRECT CONFLICTS ({len(conflicts)} found):")
                for conflict in conflicts:
                    print(f"    ❌ {conflict['source']} → {conflict['destination']} (exists in navigation)")
            else:
                print("\n✅ No navigation-redirect conflicts found!")
            
            # Invalid redirects
            invalid = validation_results['invalid_redirects']
            if invalid:
                print(f"\n⚠️  INVALID REDIRECTS ({len(invalid)} found):")
                for redirect in invalid:
                    print(f"    ❌ Source: '{redirect.get('source', '')}' → Destination: '{redirect.get('destination', '')}'")
            else:
                print("\n✅ No invalid redirects found!")
            
            # Missing navigation files
            missing_nav = validation_results['missing_navigation_files']
            if missing_nav:
                print(f"\n⚠️  MISSING NAVIGATION FILES ({len(missing_nav)} found):")
                for missing_file in missing_nav:
                    print(f"    ❌ {missing_file} (referenced in navigation but file doesn't exist)")
            else:
                print("\n✅ All navigation files exist!")
            
            # Missing redirect destinations
            missing_destinations = validation_results['missing_redirect_destinations']
            if missing_destinations:
                print(f"\n⚠️  MISSING REDIRECT DESTINATIONS ({len(missing_destinations)} found):")
                for missing_dest in missing_destinations:
                    print(f"    ❌ {missing_dest['source']} → {missing_dest['destination']} (destination file doesn't exist)")
            else:
                print("\n✅ All redirect destinations exist!")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if not args.images_only:
        if broken_links:
            print(f"❌ Found {total_broken_links} broken internal links in {len(broken_links)} files")
        else:
            print("✅ No broken internal links found!")
    
    if not args.links_only:
        if broken_images:
            print(f"❌ Found {total_broken_images} broken image references in {len(broken_images)} files")
        else:
            print("✅ No broken image references found!")

    if args.external_links or args.external_only:
        if external_results:
            failed_count = sum(1 for results in external_results.values() for r in results if not r['accessible'])
            if failed_count:
                print(f"❌ Found {failed_count} broken external links")
            else:
                print("✅ All external links are reachable!")
        else:
            print("✅ No external links found!")

    if args.check_anchors:
        if broken_anchors:
            total_broken_anchors = sum(len(v) for v in broken_anchors.values())
            print(f"❌ Found {total_broken_anchors} broken anchor fragments in {len(broken_anchors)} files")
        else:
            print("✅ No broken anchor fragments found!")

    if validation_results and 'error' not in validation_results:
        total_issues = (len(validation_results['self_referencing_redirects']) +
                       len(validation_results['navigation_redirect_conflicts']) +
                       len(validation_results['invalid_redirects']))
        if total_issues > 0:
            print(f"❌ Found {total_issues} redirect validation issues")
        else:
            print("✅ No redirect validation issues found!")

    if args.verbose:
        print(f"\nScanned files in: {args.directory}")
        print(f"Total MDX files processed: {len(glob.glob(os.path.join(args.directory, '**/*.mdx'), recursive=True))}")

    # Return non-zero exit code if any issues found
    has_broken_links = broken_links and not args.images_only
    has_broken_images = broken_images and not args.links_only
    has_broken_anchors = bool(broken_anchors) and args.check_anchors
    has_broken_external = bool(external_results) and any(
        not result['accessible']
        for results in external_results.values()
        for result in results
    )
    has_validation_issues = (validation_results and 'error' not in validation_results and
                           (validation_results['self_referencing_redirects'] or
                            validation_results['navigation_redirect_conflicts'] or
                            validation_results['invalid_redirects'] or
                            validation_results['missing_navigation_files'] or
                            validation_results['missing_redirect_destinations']))

    return 1 if (has_broken_links or has_broken_images or has_broken_anchors or has_broken_external or has_validation_issues) else 0

if __name__ == '__main__':
    exit(main())
