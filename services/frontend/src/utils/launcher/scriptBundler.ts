/**
 * Script bundler - handles Python script processing and import inlining
 */

/**
 * Remove content between #//# markers
 */
export function removeMarkedBlocks(content: string): string {
  return content.replace(/(#\/\/#)(.*?)#\/\/#/gs, '$1\n#//#')
}

/**
 * Check if a module should be inlined based on its path
 */
function shouldInlineModule(modulePath: string): boolean {
  const pathParts = modulePath.split('/')
  const fileName = pathParts[pathParts.length - 1]

  const inAddonFolder = pathParts.includes('addon')

  const startsWithCtx = fileName.startsWith('ctx')

  return inAddonFolder || startsWithCtx
}

/**
 * Recursively inline imports from addon, workbench, bootloader folders
 * or files starting with 'ctx'
 */
export function inlineImportsRecursively(
  fileContent: string,
  _filePath: string,
  getFileContent: (path: string) => string | undefined,
  processedFiles: Set<string> = new Set(),
  rootDir: string = ''
): string {
  const codeLines = fileContent.split('\n')
  const importPattern = /^\s*from\s+([\w.]+)\s+import\s+([\w*,\s]+)/
  const newCodeLines: string[] = []

  for (const line of codeLines) {
    const match = line.match(importPattern)

    if (match) {
      const moduleName = match[1]
      const modulePath = moduleName.replace(/\./g, '/') + '.py'
      const fullModulePath = rootDir ? `${rootDir}/${modulePath}` : modulePath
      const moduleContent = getFileContent(fullModulePath)

      if (moduleContent !== undefined && shouldInlineModule(fullModulePath)) {
        if (!processedFiles.has(fullModulePath)) {
          processedFiles.add(fullModulePath)
          const inlinedModule = inlineImportsRecursively(
            moduleContent,
            fullModulePath,
            getFileContent,
            processedFiles,
            rootDir
          )
          newCodeLines.push(`\n# Start of ${moduleName}.py`)
          newCodeLines.push(inlinedModule)
          newCodeLines.push(`\n# End of ${moduleName}.py\n`)
          continue
        } else {
          // Module already inlined, skip import
          continue
        }
      }
    }

    newCodeLines.push(line)
  }

  return newCodeLines.join('\n')
}

/**
 * Bundle a script with all processing steps
 */
export function bundleScript(
  scriptContent: string,
  scriptPath: string,
  getFileContent: (path: string) => string | undefined,
  rootDir: string
): string {
  let content = inlineImportsRecursively(
    scriptContent,
    scriptPath,
    getFileContent,
    new Set(),
    rootDir
  )

  content = removeMarkedBlocks(content)

  return content
}
