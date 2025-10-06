import fs from "fs";
import path from "path";

// === CONFIG ===
const ROOT_DIR = process.cwd(); // where script is run
const BASE_URL = "https://tyk.io/docs"; // must match addCanonical.js

// Recursively find all .mdx files excluding "snippets" folder
function findMdxFiles(dir) {
  let results = [];
  const files = fs.readdirSync(dir, { withFileTypes: true });

  for (const file of files) {
    const fullPath = path.join(dir, file.name);

    if (file.isDirectory()) {
      if (file.name === "snippets") continue;
      results = results.concat(findMdxFiles(fullPath));
    } else if (file.isFile() && file.name.endsWith(".mdx")) {
      results.push(fullPath);
    }
  }
  return results;
}

// Verify canonical field correctness
function verifyCanonical(filePath) {
  const content = fs.readFileSync(filePath, "utf8");

  // Extract frontmatter
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) {
    return { file: filePath, error: "❌ Missing frontmatter" };
  }

  const frontmatter = frontmatterMatch[1];

  // Match canonical line
  const canonicalMatch = frontmatter.match(/^canonical\s*:\s*"(.*?)"$/m);
  if (!canonicalMatch) {
    return { file: filePath, error: "❌ Missing canonical field" };
  }

  const canonicalValue = canonicalMatch[1];

  // Expected canonical
  const relativePath = path.relative(ROOT_DIR, filePath);
  const cleanPath = relativePath.replace(/\\/g, "/").replace(/\.mdx$/, "");
  const expected = `${BASE_URL}/${cleanPath}`;

  if (canonicalValue.endsWith(".mdx")) {
    return { file: filePath, error: `❌ Canonical ends with .mdx (${canonicalValue})` };
  }

  if (canonicalValue !== expected) {
    return {
      file: filePath,
      error: `❌ Canonical mismatch\n   Found: ${canonicalValue}\nExpected: ${expected}`,
    };
  }

  return { file: filePath, ok: true };
}

// === MAIN ===
(function main() {
  console.log("🧪 Verifying canonical fields in .mdx files...");
  const mdxFiles = findMdxFiles(ROOT_DIR);

  let passed = 0;
  let failed = 0;
  const errors = [];

  for (const file of mdxFiles) {
    const result = verifyCanonical(file);
    if (result.ok) {
      console.log(`✅ OK: ${file}`);
      passed++;
    } else {
      console.error(`${result.error} -> ${file}`);
      errors.push(result);
      failed++;
    }
  }

  console.log("\n=== SUMMARY ===");
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);

  if (failed > 0) {
    console.log("\nDetailed issues:");
    for (const err of errors) {
      console.log(`- ${err.file}: ${err.error}`);
    }
    process.exitCode = 1;
  } else {
    console.log("🎉 All canonical fields look good!");
  }
})();
