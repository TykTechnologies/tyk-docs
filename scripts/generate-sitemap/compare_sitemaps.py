import xml.etree.ElementTree as ET
from pathlib import Path

ROOT_DIR = Path.cwd()
GENERATED_SITEMAP = ROOT_DIR / "sitemap.xml"
REAL_SITEMAP = ROOT_DIR / "real.xml"

def extract_urls_from_xml(xml_path):
    """Extract all URLs from a sitemap XML file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Handle both with and without <root> wrapper
    urlset = root.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    if urlset is None:
        # If no <root> wrapper, root itself might be urlset
        urlset = root
    
    urls = set()
    for url in urlset.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc is not None and loc.text:
            urls.add(loc.text.strip())
    
    return urls

def main():
    print("=" * 80)
    print("SITEMAP COMPARISON REPORT")
    print("=" * 80)
    print()
    
    # Extract URLs from both files
    print("📊 Extracting URLs from both sitemaps...")
    generated_urls = extract_urls_from_xml(GENERATED_SITEMAP)
    real_urls = extract_urls_from_xml(REAL_SITEMAP)
    
    print(f"✅ Generated sitemap contains: {len(generated_urls)} URLs")
    print(f"✅ Real sitemap contains: {len(real_urls)} URLs")
    print()
    
    # Find differences
    only_in_generated = generated_urls - real_urls
    only_in_real = real_urls - generated_urls
    common_urls = generated_urls & real_urls
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"📈 Common URLs (in both): {len(common_urls)}")
    print(f"➕ URLs only in GENERATED sitemap: {len(only_in_generated)}")
    print(f"➖ URLs only in REAL sitemap: {len(only_in_real)}")
    print()
    
    # Show URLs only in generated
    if only_in_generated:
        print("=" * 80)
        print("URLs ONLY IN GENERATED SITEMAP (not in real)")
        print("=" * 80)
        for url in sorted(only_in_generated)[:50]:  # Show first 50
            print(f"  ➕ {url}")
        if len(only_in_generated) > 50:
            print(f"  ... and {len(only_in_generated) - 50} more")
        print()
    
    # Show URLs only in real
    if only_in_real:
        print("=" * 80)
        print("URLs ONLY IN REAL SITEMAP (missing from generated)")
        print("=" * 80)
        for url in sorted(only_in_real)[:50]:  # Show first 50
            print(f"  ➖ {url}")
        if len(only_in_real) > 50:
            print(f"  ... and {len(only_in_real) - 50} more")
        print()
    
    # Calculate match percentage
    if real_urls:
        match_percentage = (len(common_urls) / len(real_urls)) * 100
        print("=" * 80)
        print("MATCH ANALYSIS")
        print("=" * 80)
        print(f"✅ Match percentage: {match_percentage:.2f}%")
        print(f"   ({len(common_urls)} out of {len(real_urls)} URLs from real sitemap)")
        print()
    
    # Verdict
    print("=" * 80)
    print("VERDICT")
    print("=" * 80)
    if only_in_generated and not only_in_real:
        print("⚠️  Your generated sitemap has EXTRA URLs not in the live site")
    elif only_in_real and not only_in_generated:
        print("⚠️  Your generated sitemap is MISSING URLs from the live site")
    elif only_in_generated and only_in_real:
        print("⚠️  Your generated sitemap has BOTH missing and extra URLs")
    else:
        print("✅ Perfect match! Your sitemap matches the live site exactly!")
    print("=" * 80)

if __name__ == "__main__":
    main()
