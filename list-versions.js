const fs = require("fs");
const path = require("path");

function findPackageJson(startDir) {
  let results = [];
  for (const file of fs.readdirSync(startDir)) {
    const full = path.join(startDir, file);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (file === "node_modules" || file === ".git") continue;

      const pkgPath = path.join(full, "package.json");
      if (fs.existsSync(pkgPath)) {
        const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf8"));
        results.push({
          name: pkg.name,
          version: pkg.version,
          path: full
        });
      }
      results = results.concat(findPackageJson(full));
    }
  }

  return results;
}
const list = findPackageJson(process.cwd())
console.table(list);
