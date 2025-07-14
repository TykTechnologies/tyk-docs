#!/usr/bin/env python3
"""
Browser-Based Site Content Analyzer

This script uses a headless browser (Puppeteer) to analyze documentation sites
by visiting each page, waiting for content to render, and examining the final HTML.
Perfect for Next.js sites with client-side rendering or dynamic content.

USAGE:
    pip install pyppeteer beautifulsoup4
    python browser_site_analyzer.py --base-url http://localhost:3000 --docs-json mintlify-poc/docs.json
    
FEATURES:
    - Uses headless browser for accurate content rendering
    - Waits for .mdx-content divs to load with actual content
    - Configurable wait times and timeouts
    - Handles JavaScript-rendered content properly
    - Same analysis logic as curl version but more reliable
    - Optional screenshots on failures
"""

import json
import os
import asyncio
import argparse
import time
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re

try:
    from pyppeteer import launch
    from pyppeteer.errors import TimeoutError as PuppeteerTimeoutError
except ImportError:
    print("❌ pyppeteer not installed. Run: pip install pyppeteer")
    exit(1)

class BrowserSiteAnalyzer:
    def __init__(self, base_url, output_dir="site_download", wait_time=4, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.wait_time = wait_time  # Time to wait after page load
        self.timeout = timeout * 1000  # Convert to milliseconds for Puppeteer
        self.browser = None
        self.results = {
            'summary': {
                'total_pages_visited': 0,
                'total_pages_analyzed': 0,
                'pages_with_empty_content': 0,
                'pages_with_sufficient_content': 0,
                'browser_failures': 0
            },
            'empty_pages': [],
            'healthy_pages': [],
            'browser_failures': []
        }
    
    def get_urls_from_docs_json(self, docs_json_path):
        """Extract URLs from docs.json navigation structure."""
        urls = []
        
        try:
            print(f"Loading navigation from: {docs_json_path}")
            with open(docs_json_path, 'r') as f:
                docs_data = json.load(f)
            
            def extract_urls_recursive(nav_item, base_url):
                """Recursively extract URLs from navigation structure."""
                extracted = []
                
                if isinstance(nav_item, dict):
                    # Check if this item has a page URL
                    if 'page' in nav_item:
                        page_url = nav_item['page']
                        if not page_url.startswith('http'):
                            page_url = f"{base_url}/{page_url.lstrip('/')}"
                        extracted.append(page_url)
                    
                    # Check for nested navigation
                    if 'pages' in nav_item:
                        for sub_item in nav_item['pages']:
                            extracted.extend(extract_urls_recursive(sub_item, base_url))
                    
                elif isinstance(nav_item, str):
                    # Direct page reference
                    if not nav_item.startswith('http'):
                        nav_item = f"{base_url}/{nav_item.lstrip('/')}"
                    extracted.append(nav_item)
                
                return extracted
            
            # Extract URLs from navigation
            if 'navigation' in docs_data:
                navigation = docs_data['navigation']
                
                # Handle different navigation structures
                if 'tabs' in navigation:
                    # Mintlify structure with tabs
                    for tab in navigation['tabs']:
                        if 'pages' in tab:
                            for page in tab['pages']:
                                urls.extend(extract_urls_recursive(page, self.base_url))
                        if 'groups' in tab:
                            for group in tab['groups']:
                                if 'pages' in group:
                                    for page in group['pages']:
                                        urls.extend(extract_urls_recursive(page, self.base_url))
                elif isinstance(navigation, list):
                    # Direct list of navigation items
                    for nav_item in navigation:
                        urls.extend(extract_urls_recursive(nav_item, self.base_url))
                else:
                    # Other navigation structures
                    urls.extend(extract_urls_recursive(navigation, self.base_url))
            
            # Also add the home page
            urls.insert(0, self.base_url)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            print(f"Found {len(unique_urls)} URLs in docs.json")
            return unique_urls
            
        except Exception as e:
            print(f"Failed to parse docs.json: {e}")
            return []
    
    def url_to_filename(self, url):
        """Convert URL to a safe filename."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            return "index.html"
        
        # Replace path separators with underscores
        filename = path.replace('/', '_')
        
        # Add .html extension if not present
        if not filename.endswith('.html'):
            filename += '.html'
        
        # Remove any unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        return filename
    
    async def init_browser(self):
        """Initialize the browser instance."""
        print("🚀 Launching headless browser...")
        self.browser = await launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-default-apps'
            ]
        )
        print("✅ Browser launched successfully")
    
    async def close_browser(self):
        """Close the browser instance."""
        if self.browser:
            await self.browser.close()
            print("🔒 Browser closed")
    
    async def download_page_with_browser(self, url):
        """Download and render a single page using browser."""
        filename = self.url_to_filename(url)
        filepath = self.output_dir / filename
        
        print(f"🌐 Visiting: {url} -> {filename}")
        
        page = None
        try:
            # Create new page
            page = await self.browser.newPage()
            
            # Set viewport and user agent
            await page.setViewport({'width': 1280, 'height': 720})
            await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Navigate to the page
            print(f"   📄 Loading page...")
            response = await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': self.timeout})
            
            if not response or response.status >= 400:
                error_msg = f"HTTP {response.status if response else 'No response'}"
                print(f"   ❌ Failed to load: {error_msg}")
                return filepath, False, error_msg
            
            print(f"   ⏳ Waiting for content to render...")
            
            # Wait for .mdx-content div to appear
            try:
                await page.waitForSelector('div[class*="mdx-content"]', {'timeout': self.timeout})
                print(f"   ✅ Found .mdx-content div")
            except PuppeteerTimeoutError:
                print(f"   ⚠️  No .mdx-content div found within timeout")
            
            # Additional wait for content to load
            if self.wait_time > 0:
                print(f"   ⏱️  Waiting {self.wait_time}s for content to fully load...")
                await asyncio.sleep(self.wait_time)
            
            # Try to wait for meaningful content in .mdx-content div
            try:
                await page.waitForFunction(
                    '''() => {
                        const mdxDiv = document.querySelector('div[class*="mdx-content"]');
                        if (!mdxDiv) return false;
                        const text = mdxDiv.innerText.trim();
                        return text.length > 50; // Wait for at least 50 characters
                    }''',
                    {'timeout': 5000}  # 5 second timeout for content
                )
                print(f"   ✅ Content loaded successfully")
            except PuppeteerTimeoutError:
                print(f"   ⚠️  Content may still be loading...")
            
            # Get the final HTML content
            html_content = await page.content()
            
            # Save HTML to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"   ✅ Page saved: {filename}")
            return filepath, True, None
            
        except PuppeteerTimeoutError as e:
            error_msg = f"Browser timeout: {str(e)}"
            print(f"   ❌ Timeout: {error_msg}")
            return filepath, False, error_msg
            
        except Exception as e:
            error_msg = f"Browser error: {str(e)}"
            print(f"   ❌ Error: {error_msg}")
            return filepath, False, error_msg
            
        finally:
            if page:
                await page.close()
    
    def analyze_html_content(self, filepath, url):
        """Analyze downloaded HTML file for content issues."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Get page title
            title_tag = soup.find('title')
            page_title = title_tag.get_text().strip() if title_tag else "Unknown"
            
            # Look for .mdx-content div specifically
            mdx_content_div = soup.find('div', class_=lambda x: x and 'mdx-content' in x)
            
            page_info = {
                'url': url,
                'filename': filepath.name,
                'title': page_title,
                'has_mdx_content_div': mdx_content_div is not None,
                'mdx_content_length': 0,
                'mdx_content_text': '',
                'total_body_length': 0,
                'meaningful_words': 0,
                'is_empty': False,
                'issues': []
            }
            
            # Analyze .mdx-content div
            if mdx_content_div:
                mdx_text = mdx_content_div.get_text().strip()
                page_info['mdx_content_length'] = len(mdx_text)
                page_info['mdx_content_text'] = mdx_text[:200]  # First 200 chars for preview
                
                # Count meaningful words in mdx content
                words = mdx_text.split()
                meaningful_words = [w for w in words if len(w) > 3 and w.isalpha()]
                page_info['meaningful_words'] = len(meaningful_words)
                
                # Check if content is empty or insufficient
                if len(mdx_text) == 0:
                    page_info['is_empty'] = True
                    page_info['issues'].append("MDX content div is completely empty")
                elif len(meaningful_words) < 15:
                    page_info['is_empty'] = True
                    page_info['issues'].append(f"MDX content has only {len(meaningful_words)} meaningful words (need 15+)")
                elif len(mdx_text) < 100:
                    page_info['is_empty'] = True
                    page_info['issues'].append(f"MDX content is very short ({len(mdx_text)} characters)")
            else:
                page_info['is_empty'] = True
                page_info['issues'].append("No .mdx-content div found")
            
            # Also analyze total body content for comparison
            body = soup.find('body')
            if body:
                body_text = body.get_text().strip()
                page_info['total_body_length'] = len(body_text)
            
            return page_info
            
        except Exception as e:
            return {
                'url': url,
                'filename': filepath.name,
                'title': 'Error',
                'has_mdx_content_div': False,
                'mdx_content_length': 0,
                'mdx_content_text': '',
                'total_body_length': 0,
                'meaningful_words': 0,
                'is_empty': True,
                'issues': [f"Error analyzing HTML: {str(e)}"]
            }
    
    async def visit_and_analyze_site(self, urls):
        """Visit all pages with browser and analyze their content."""
        print(f"\n🚀 Starting browser analysis of {len(urls)} pages...")
        print(f"📁 Saving files to: {self.output_dir}")
        print(f"⏱️  Wait time per page: {self.wait_time}s")
        print(f"⏰ Timeout per page: {self.timeout/1000}s")
        
        # Initialize browser
        await self.init_browser()
        
        try:
            for i, url in enumerate(urls, 1):
                print(f"\n[{i}/{len(urls)}] Processing: {url}")
                
                # Visit the page with browser
                filepath, success, error = await self.download_page_with_browser(url)
                
                if success:
                    self.results['summary']['total_pages_visited'] += 1
                    
                    # Analyze the downloaded HTML
                    page_info = self.analyze_html_content(filepath, url)
                    self.results['summary']['total_pages_analyzed'] += 1
                    
                    # Categorize the results
                    if page_info['is_empty']:
                        self.results['empty_pages'].append(page_info)
                        self.results['summary']['pages_with_empty_content'] += 1
                        print(f"   ❌ Empty content: {page_info['issues']}")
                    else:
                        self.results['healthy_pages'].append(page_info)
                        self.results['summary']['pages_with_sufficient_content'] += 1
                        print(f"   ✅ Good content: {page_info['meaningful_words']} words, {page_info['mdx_content_length']} chars")
                else:
                    self.results['browser_failures'].append({
                        'url': url,
                        'error': error
                    })
                    self.results['summary']['browser_failures'] += 1
        
        finally:
            # Close browser
            await self.close_browser()
        
        return self.results
    
    def print_summary_report(self):
        """Print a comprehensive summary of the analysis."""
        summary = self.results['summary']
        
        print("\n" + "="*80)
        print("BROWSER-BASED SITE CONTENT ANALYSIS SUMMARY")
        print("="*80)
        print(f"Total pages visited: {summary['total_pages_visited']}")
        print(f"Total pages analyzed: {summary['total_pages_analyzed']}")
        print(f"Pages with empty/insufficient content: {summary['pages_with_empty_content']}")
        print(f"Pages with sufficient content: {summary['pages_with_sufficient_content']}")
        print(f"Browser failures: {summary['browser_failures']}")
        print()
        
        if self.results['empty_pages']:
            print("🚨 PAGES WITH EMPTY OR INSUFFICIENT CONTENT:")
            print()
            
            for page in self.results['empty_pages']:
                print(f"❌ {page['url']}")
                print(f"   Title: {page['title']}")
                print(f"   File: {page['filename']}")
                print(f"   MDX content length: {page['mdx_content_length']} characters")
                print(f"   Meaningful words: {page['meaningful_words']}")
                print(f"   Has .mdx-content div: {page['has_mdx_content_div']}")
                if page['mdx_content_text']:
                    print(f"   Content preview: {page['mdx_content_text'][:100]}...")
                print(f"   Issues: {', '.join(page['issues'])}")
                print()
        
        if self.results['browser_failures']:
            print("🚨 BROWSER FAILURES:")
            print()
            
            for failure in self.results['browser_failures']:
                print(f"❌ {failure['url']}")
                print(f"   Error: {failure['error']}")
                print()
        
        if summary['pages_with_sufficient_content'] > 0:
            print("✅ PAGES WITH GOOD CONTENT:")
            print()
            
            for page in self.results['healthy_pages'][:5]:  # Show first 5
                print(f"✅ {page['url']}")
                print(f"   Title: {page['title']}")
                print(f"   MDX content: {page['mdx_content_length']} chars, {page['meaningful_words']} words")
                if page['mdx_content_text']:
                    print(f"   Preview: {page['mdx_content_text'][:100]}...")
                print()
            
            if len(self.results['healthy_pages']) > 5:
                print(f"   ... and {len(self.results['healthy_pages']) - 5} more pages with good content")
                print()
        
        print("="*80)
        print(f"RESULT: {summary['pages_with_empty_content']} pages have content issues out of {summary['total_pages_analyzed']} analyzed")
        print("="*80)
    
    def save_detailed_report(self, output_file="browser_analysis_report.json"):
        """Save detailed results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed report saved to: {output_file}")

async def main():
    """Main function to run the browser-based site analyzer."""
    parser = argparse.ArgumentParser(description='Browser-based site content analyzer')
    parser.add_argument('--base-url', default='http://localhost:3000', 
                       help='Base URL of the website to analyze')
    parser.add_argument('--docs-json', required=True,
                       help='Path to docs.json file')
    parser.add_argument('--output-dir', default='site_download',
                       help='Directory to save downloaded HTML files')
    parser.add_argument('--report-file', default='browser_analysis_report.json',
                       help='Output file for detailed JSON report')
    parser.add_argument('--wait-time', type=int, default=4,
                       help='Time to wait after page load (seconds)')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for page operations (seconds)')
    
    args = parser.parse_args()
    
    print("🔍 Browser-Based Site Content Analyzer")
    print(f"📍 Base URL: {args.base_url}")
    print(f"📋 Docs JSON: {args.docs_json}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"⏱️  Wait time: {args.wait_time}s")
    print(f"⏰ Timeout: {args.timeout}s")
    
    # Initialize analyzer
    analyzer = BrowserSiteAnalyzer(
        args.base_url, 
        args.output_dir, 
        args.wait_time, 
        args.timeout
    )
    
    # Get URLs from docs.json
    urls = analyzer.get_urls_from_docs_json(args.docs_json)
    
    if not urls:
        print("❌ No URLs found in docs.json. Exiting.")
        return
    
    # Visit and analyze all pages
    results = await analyzer.visit_and_analyze_site(urls)
    
    # Print summary report
    analyzer.print_summary_report()
    
    # Save detailed report
    analyzer.save_detailed_report(args.report_file)
    
    print(f"\n🎯 Analysis complete! Check {args.output_dir}/ for downloaded HTML files.")

if __name__ == "__main__":
    asyncio.run(main())
