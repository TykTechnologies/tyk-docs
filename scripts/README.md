# Site Content Analysis Scripts

This directory contains scripts for analyzing the content quality of the Tyk documentation site.

## Browser Site Analyzer

The `browser_site_analyzer.py` script uses a headless browser to analyze documentation pages for content rendering issues, specifically designed for Next.js/Mintlify sites.

### Features

- **Browser-based analysis**: Uses Puppeteer to properly render JavaScript-generated content
- **Smart content detection**: Waits for `.mdx-content` divs to load with meaningful content
- **Configurable timing**: Adjustable wait times and timeouts for different site speeds
- **Comprehensive reporting**: Detailed analysis with statistics and issue identification
- **Production-ready**: Designed to work with https://tyk.mintlify.app

### Local Usage

```bash
# Install dependencies
pip install pyppeteer beautifulsoup4

# Run analysis on production site
python scripts/browser_site_analyzer.py \
  --base-url https://tyk.mintlify.app \
  --docs-json docs.json \
  --wait-time 3 \
  --timeout 30

# Run analysis on local development server
python scripts/browser_site_analyzer.py \
  --base-url http://localhost:3000 \
  --docs-json docs.json \
  --wait-time 1 \
  --timeout 20
```

### Parameters

- `--base-url`: Base URL of the website to analyze (default: http://localhost:3000)
- `--docs-json`: Path to docs.json file (required)
- `--output-dir`: Directory to save downloaded HTML files (default: site_download)
- `--report-file`: Output file for detailed JSON report (default: browser_analysis_report.json)
- `--wait-time`: Time to wait after page load in seconds (default: 4)
- `--timeout`: Timeout for page operations in seconds (default: 30)

### GitHub Action

The analysis can also be run automatically via GitHub Actions:

1. Go to the **Actions** tab in the repository
2. Select **"Site Content Analysis"** workflow
3. Click **"Run workflow"**
4. Optionally adjust timing parameters:
   - **Wait time**: 2-4 seconds (recommended for production)
   - **Timeout**: 30-45 seconds
5. View results in the action summary

### Output

The script generates:

- **Console output**: Real-time progress and summary statistics
- **HTML files**: Downloaded pages for manual inspection (in `site_analysis_output/`)
- **JSON report**: Detailed analysis results (`site_analysis_report.json`)
- **GitHub summary**: Formatted results in GitHub Actions (when run via workflow)

### Content Quality Criteria

Pages are flagged as having issues if they have:
- No `.mdx-content` div found
- Empty `.mdx-content` div
- Less than 15 meaningful words (>3 characters, alphabetic)
- Less than 100 total characters in content

### Timing Recommendations

**For localhost development:**
- `--wait-time 1` (fast local rendering)
- `--timeout 20` (local network is fast)

**For production sites:**
- `--wait-time 3` (allow for CDN/network delays)
- `--timeout 30` (account for slower responses)

**For slow or heavily loaded sites:**
- `--wait-time 4-6` (extra time for content loading)
- `--timeout 45-60` (generous timeout for reliability)

### Troubleshooting

**"No URLs found in docs.json"**
- Verify the docs.json file path is correct
- Check that docs.json contains a valid navigation structure

**Browser timeout errors**
- Increase `--timeout` value
- Check if the target site is accessible
- Verify network connectivity

**Empty content detected**
- Increase `--wait-time` to allow more time for content loading
- Check if the site uses client-side rendering that needs more time
- Manually verify the page loads correctly in a browser

**Package installation issues**
- Run: `pip install pyppeteer beautifulsoup4`
- On first run, pyppeteer will download Chromium automatically
- Ensure you have sufficient disk space for Chromium download
