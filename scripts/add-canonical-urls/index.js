import fs from "fs";
import path from "path";

// === CONFIG ===
const ROOT_DIR = process.cwd(); // where the program is running
const BASE_URL = "https://tyk.io/docs"; // canonical base

// Recursively find all .mdx files excluding "snippets" folder
function findMdxFiles(dir) {
  let results = [];
  const files = fs.readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = path.join(dir, file.name);

    // Skip "snippets" directory
    if (file.isDirectory()) {
      if (file.name === "snippets") continue;
      results = results.concat(findMdxFiles(fullPath));
    } else if (file.isFile() && file.name.endsWith(".mdx")) {
      results.push(fullPath);
    }
  }
  return results;
}

// Add canonical field before ending "---" in frontmatter
function addCanonicalToFrontmatter(filePath) {
  const content = fs.readFileSync(filePath, "utf8");

  // Frontmatter regex: between --- and ---
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) {
    console.warn(`⚠️  No frontmatter found in: ${filePath}`);
    return;
  }

  const frontmatter = frontmatterMatch[1];

  // Skip if canonical already exists
  if (/^canonical\s*:|["']canonical["']\s*:/m.test(frontmatter)) {
    console.log(`✅ Canonical already present in: ${filePath}`);
    return;
  }

  // Build canonical URL
  const relativePath = path.relative(ROOT_DIR, filePath);
  const cleanPath = relativePath.replace(/\\/g, "/").replace(/\.mdx$/, "");
  const canonicalUrl = `${BASE_URL}/${cleanPath}`;

  // Insert canonical before ending triple dash
  const newFrontmatter =
    frontmatter + `\ncanonical: "${canonicalUrl}"`;

  const newContent = content.replace(
    /^---\n([\s\S]*?)\n---/,
    `---\n${newFrontmatter}\n---`
  );

  fs.writeFileSync(filePath, newContent, "utf8");
  console.log(`📝 Added canonical to: ${filePath}`);
}

// === MAIN ===
(function main() {
  console.log("🔍 Searching for .mdx files...");
  const mdxFiles = findMdxFiles(ROOT_DIR);

  console.log(`Found ${mdxFiles.length} .mdx files`);
  mdxFiles.forEach(addCanonicalToFrontmatter);
})();
