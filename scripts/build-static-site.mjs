import { access, cp, mkdir, readdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "dist");

const excludedRootDirectories = new Set([
  ".bundle",
  ".git",
  ".github",
  ".jekyll-cache",
  ".sass-cache",
  ".vercel",
  ".vscode",
  "_posts",
  "_site",
  "__pycache__",
  "dist",
  "docs",
  "node_modules",
  "scripts",
  "services",
  "supabase",
  "tests",
  "vendor",
]);

const excludedRootFiles = new Set([
  ".python-version",
  "Dockerfile",
  "LICENSE",
  "app.py",
  "package-lock.json",
  "package.json",
  "pyproject.toml",
  "render.yaml",
  "requirements-dev.txt",
  "requirements.txt",
  "vercel.json",
]);

const excludedExtensions = new Set([
  ".lock",
  ".md",
  ".py",
  ".pyc",
  ".sql",
  ".toml",
  ".yaml",
  ".yml",
]);

const copiedFiles = [];

async function copyPublicFiles(source, destination, relativePath = "") {
  await mkdir(destination, { recursive: true });
  const entries = await readdir(source, { withFileTypes: true });

  for (const entry of entries) {
    const relative = path.join(relativePath, entry.name);

    if (!relativePath && entry.isDirectory() && excludedRootDirectories.has(entry.name)) {
      continue;
    }

    if (!relativePath && entry.isFile() && excludedRootFiles.has(entry.name)) {
      continue;
    }

    if (entry.isFile() && excludedExtensions.has(path.extname(entry.name).toLowerCase())) {
      continue;
    }

    if (entry.isSymbolicLink()) {
      continue;
    }

    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);

    if (entry.isDirectory()) {
      await copyPublicFiles(sourcePath, destinationPath, relative);
      continue;
    }

    if (entry.isFile()) {
      await cp(sourcePath, destinationPath);
      copiedFiles.push(relative.replaceAll("\\", "/"));
    }
  }
}

await rm(output, { recursive: true, force: true });
await copyPublicFiles(root, output);

const requiredFiles = [
  ".well-known/security.txt",
  "404.html",
  "blog/index.html",
  "cv/index.html",
  "index.html",
  "privacy/index.html",
  "robots.txt",
  "signup/index.html",
  "sitemap.xml",
  "styles.css",
];

for (const requiredFile of requiredFiles) {
  await access(path.join(output, requiredFile));
}

console.log(`Prepared ${copiedFiles.length} public files in dist/.`);
