import fs from "fs";
import path from "path";

// === CONFIG ===
const ROOT_DIR = process.cwd(); // where the program is running
const BASE_URL = "https://tyk.io/docs"; // canonical base

// Recursively find all .mdx files excluding any "snippets" folder
function findMdxFiles(dir) {
  let results = [];
  const files = fs.readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = path.join(dir, file.name);

    // Skip "snippets" directory and any of its contents
    if (file.isDirectory()) {
      if (file.name === "snippets") {
        console.log(`⏩ Skipping directory (and all inside): ${fullPath}`);
        continue;
      }
      results = results.concat(findMdxFiles(fullPath));
    } else if (file.isFile() && file.name.endsWith(".mdx")) {
      // Double-check exclusion: if path contains /snippets/ anywhere, skip it
      const parts = fullPath.split(path.sep);
      if (parts.includes("snippets")) {
        console.log(`⏩ Skipping file inside snippets: ${fullPath}`);
        continue;
      }
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

  // Build canonical URL
  const relativePath = path.relative(ROOT_DIR, filePath);
  const cleanPath = relativePath.replace(/\\/g, "/").replace(/\.mdx$/, "");
  const canonicalUrl = `${BASE_URL}/${cleanPath}`;

  // If canonical exists, override it
  let newFrontmatter;
  if (/^canonical\s*:|["']canonical["']\s*:/m.test(frontmatter)) {
    newFrontmatter = frontmatter.replace(
      /^(\s*(?:["']?canonical["']?)\s*:\s*).*$/m,
      `canonical: "${canonicalUrl}"`
    );
    console.log(`🔁 Updated canonical in: ${filePath}`);
  } else {
    newFrontmatter = frontmatter + `\ncanonical: "${canonicalUrl}"`;
    console.log(`📝 Added canonical to: ${filePath}`);
  }

  const newContent = content.replace(
    /^---\n([\s\S]*?)\n---/,
    `---\n${newFrontmatter}\n---`
  );

  fs.writeFileSync(filePath, newContent, "utf8");
}

// === MAIN ===
(function main() {
  console.log("🔍 Searching for .mdx files...");
  const mdxFiles = findMdxFiles(ROOT_DIR);

  console.log(`📄 Found ${mdxFiles.length} eligible .mdx files`);
  mdxFiles.forEach(addCanonicalToFrontmatter);
})();
