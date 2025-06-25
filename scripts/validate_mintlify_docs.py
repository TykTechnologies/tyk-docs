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

3. COMPREHENSIVE CHECKS:
   - Validates all navigation links point to existing files
   - Ensures all redirect destinations are valid and exist
   - Skips external URLs, anchors, and special protocols appropriately
   - Handles anchor fragments and query parameters correctly

USAGE:
   python validate_mintlify_docs.py [directory] [options]
   make check-redirects    # Validate redirects and navigation only
   make validate-all       # Full validation with verbose output
"""

import os
import re
import glob
import json
import argparse
import urllib.parse
from pathlib import Path
from typing import Set, List, Tuple, Dict, Any

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

def find_internal_links(mdx_content: str) -> Set[str]:
    """Extract all internal links from MDX content, excluding links in comments and code blocks."""
    # Remove comments and code blocks first to avoid parsing commented-out or code example links
    clean_content = remove_comments_and_code(mdx_content)
    
    internal_links = set()
    
    # Pattern for markdown links: [text](path) - exclude external URLs
    markdown_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
    
    # Pattern for HTML anchor tags: <a href="path">
    html_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
    
    # Find all matches
    for pattern in [markdown_pattern, html_pattern]:
        matches = re.findall(pattern, clean_content, re.IGNORECASE)
        for match in matches:
            # For markdown pattern, match[1] is the URL, for HTML pattern, match is the URL
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
    
    # Find all matches
    for pattern in [markdown_pattern, html_pattern, jsx_pattern]:
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

def scan_mdx_files(directory: str) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Scan all MDX files and return links and images by file."""
    file_links = {}
    file_images = {}
    mdx_files = glob.glob(os.path.join(directory, '**/*.mdx'), recursive=True)
    
    print(f"Scanning {len(mdx_files)} MDX files for links and images...")
    
    for mdx_file in mdx_files:
        try:
            with open(mdx_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Get relative path for reporting
                rel_path = os.path.relpath(mdx_file, directory)
                
                # Find links and images
                links = find_internal_links(content)
                images = find_image_references(content)
                
                if links:
                    file_links[rel_path] = links
                if images:
                    file_images[rel_path] = images
                    
        except Exception as e:
            print(f"Error reading {mdx_file}: {e}")
    
    return file_links, file_images

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

def check_broken_links(base_dir: str) -> Tuple[Dict[str, List[str]], Dict[str, List[str]], Dict[str, str]]:
    """Check for broken internal links and missing images."""
    print(f"Checking for broken links in: {base_dir}")
    
    # Load redirects from configuration
    redirects = load_redirects(base_dir)
    
    # Scan all MDX files
    file_links, file_images = scan_mdx_files(base_dir)
    
    # Find all existing files
    existing_files = find_existing_files(base_dir)
    
    # Check for broken links
    broken_links = {}
    broken_images = {}
    
    # Check internal links
    for file_path, links in file_links.items():
        file_broken_links = []
        for link in links:
            if not check_link_exists(link, existing_files, redirects):
                file_broken_links.append(link)
        
        if file_broken_links:
            broken_links[file_path] = file_broken_links
    
    # Check image references
    for file_path, images in file_images.items():
        file_broken_images = []
        for image in images:
            if image not in existing_files:
                file_broken_images.append(image)
        
        if file_broken_images:
            broken_images[file_path] = file_broken_images
    
    return broken_links, broken_images, redirects


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
    
    args = parser.parse_args()
    
    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        return 1
    
    # Check for broken links and images
    broken_links, broken_images, redirects = check_broken_links(args.directory)
    
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
    
    if not args.images_only and broken_links:
        print(f"\n🔗 BROKEN INTERNAL LINKS ({total_broken_links} total):")
        for file_path, links in sorted(broken_links.items()):
            print(f"\n  📄 {file_path}:")
            for link in sorted(links):
                print(f"    ❌ {link}")
    
    if not args.links_only and broken_images:
        print(f"\n🖼️  BROKEN IMAGE REFERENCES ({total_broken_images} total):")
        for file_path, images in sorted(broken_images.items()):
            print(f"\n  📄 {file_path}:")
            for image in sorted(images):
                print(f"    ❌ {image}")
    
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
    has_validation_issues = (validation_results and 'error' not in validation_results and 
                           (validation_results['self_referencing_redirects'] or 
                            validation_results['navigation_redirect_conflicts'] or 
                            validation_results['invalid_redirects'] or
                            validation_results['missing_navigation_files'] or
                            validation_results['missing_redirect_destinations']))
    
    return 1 if (has_broken_links or has_broken_images or has_validation_issues) else 0

if __name__ == '__main__':
    exit(main())
