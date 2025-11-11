// remove-redirects.js
// Node.js >= 14+ (works fine on 16/18/20+)
// Usage: node remove-redirects.js
// Expects files in same directory: urls.txt and docs.json

const fs = require('fs/promises');
const path = require('path');

function normalizePath(input) {
  // Accepts either full URL or path. Returns normalized path:
  //  - ensures leading slash
  //  - strips trailing slash (unless root "/")
  //  - decodes percent-encoding (safe for most cases)
  if (!input) return '/';

  let raw = input.trim();

  // If it's just a domainless path, ensure it starts with '/'
  try {
    // If it's a full URL like https://example.com/foo?x=1#bar
    const u = new URL(raw);
    raw = u.pathname;
  } catch (e) {
    // not a full URL — maybe it's a path like "/foo" or "foo"
    if (!raw.startsWith('/')) raw = '/' + raw;
    // Remove query/hash if present accidentally (rare)
    raw = raw.split(/[?#]/)[0];
  }

  // decode percent encoded characters for matching consistency
  try {
    raw = decodeURIComponent(raw);
  } catch (e) {
    // if decode fails, keep raw
  }

  // Remove trailing slash unless it's just "/"
  if (raw.length > 1 && raw.endsWith('/')) {
    raw = raw.slice(0, -1);
  }

  return raw || '/';
}

async function main() {
  const urlsPath = path.resolve(process.cwd(), 'urls.txt');
  const docsPath = path.resolve(process.cwd(), 'docs.json');
  const outDocsPath = path.resolve(process.cwd(), 'new-docs.json');
  const notFoundPath = path.resolve(process.cwd(), 'not-found.txt');

  // Read files
  const [urlsRaw, docsRaw] = await Promise.all([
    fs.readFile(urlsPath, 'utf8'),
    fs.readFile(docsPath, 'utf8'),
  ]);

  // Parse urls.txt lines — preserve original line text for not-found output
  const urlLines = urlsRaw.split(/\r?\n/).map(l => l.trim()).filter(Boolean);

  // Build set of normalized paths from urls.txt
  const urlPathToOriginals = new Map(); // normalizedPath -> array of original lines that produced it
  for (const line of urlLines) {
    const np = normalizePath(line);
    if (!urlPathToOriginals.has(np)) urlPathToOriginals.set(np, []);
    urlPathToOriginals.get(np).push(line);
  }
  const urlPathsSet = new Set(urlPathToOriginals.keys());

  // Parse docs.json
  let docs;
  try {
    docs = JSON.parse(docsRaw);
  } catch (err) {
    console.error('Failed to parse docs.json:', err.message);
    process.exit(1);
  }

  const redirects = Array.isArray(docs.redirects) ? docs.redirects : [];

  // Build a set of redirect source paths for fast membership checks
  // Normalize redirect.source as well to avoid mismatch due to trailing slash, etc.
  const redirectSourceToIndex = new Map(); // normalizedSource -> original indices (array) (in case of duplicates)
  for (let i = 0; i < redirects.length; i++) {
    const r = redirects[i];
    if (!r || typeof r.source !== 'string') continue;
    const ns = normalizePath(r.source);
    if (!redirectSourceToIndex.has(ns)) redirectSourceToIndex.set(ns, []);
    redirectSourceToIndex.get(ns).push(i);
  }

  // Determine which url paths matched an existing redirect source
  const matchedUrlPaths = new Set();
  const notFoundOriginalUrls = [];

  for (const [np, originals] of urlPathToOriginals.entries()) {
    if (redirectSourceToIndex.has(np)) {
      matchedUrlPaths.add(np);
    } else {
      // preserve the original line(s) as provided in urls.txt
      for (const orig of originals) notFoundOriginalUrls.push(orig);
      console.log(`Not found: ${originals.join(', ')}`);
    }
  }

  // Create filtered redirects (keep only those whose normalized source is NOT in urlPathsSet)
  // This is a single-pass O(N) filter with O(1) lookups.
  const filteredRedirects = redirects.filter(r => {
    if (!r || typeof r.source !== 'string') return true; // keep malformed entries to avoid data loss
    const ns = normalizePath(r.source);
    return !urlPathsSet.has(ns);
  });

  // Build updated docs object
  const updatedDocs = { ...docs, redirects: filteredRedirects };

  // Write outputs
  await Promise.all([
    fs.writeFile(outDocsPath, JSON.stringify(updatedDocs, null, 2), 'utf8'),
    fs.writeFile(notFoundPath, notFoundOriginalUrls.join('\n'), 'utf8'),
  ]);

  const removedCount = redirects.length - filteredRedirects.length;
  console.log('--- Summary ---');
  console.log(`Total redirects in original: ${redirects.length}`);
  console.log(`Redirects removed: ${removedCount}`);
  console.log(`Redirects remaining: ${filteredRedirects.length}`);
  console.log(`Not found URLs written to: ${notFoundPath}`);
  console.log(`Updated docs written to: ${outDocsPath}`);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
