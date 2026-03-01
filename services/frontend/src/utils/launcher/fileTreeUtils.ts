import { FileNode } from '../../hooks/useFileSystem'

/**
 * Find a file in the file tree by name
 */
export function findFileByName(root: FileNode, fileName: string): FileNode | null {
  if (root.type === 'file' && root.name === fileName) {
    return root
  }
  if (root.children) {
    for (const child of root.children) {
      const found = findFileByName(child, fileName)
      if (found) return found
    }
  }
  return null
}

/**
 * Get all files with a specific extension from the tree
 */
export function getFilesByExtension(root: FileNode, extension: string): FileNode[] {
  const files: FileNode[] = []

  const traverse = (node: FileNode) => {
    if (node.type === 'file' && node.name.endsWith(extension)) {
      files.push(node)
    }
    if (node.children) {
      node.children.forEach(traverse)
    }
  }

  traverse(root)
  return files
}

/**
 * Get all Python files from the tree
 */
export function getAllPythonFiles(root: FileNode): FileNode[] {
  return getFilesByExtension(root, '.py')
}

/**
 * Build a function to get file content by path from the file tree
 */
export function createFileContentGetter(root: FileNode): (path: string) => string | undefined {
  const fileMap = new Map<string, string>()

  const traverse = (node: FileNode, currentPath: string = '') => {
    const nodePath = currentPath ? `${currentPath}/${node.name}` : node.name
    if (node.type === 'file' && node.content !== undefined) {
      // Store with multiple path variations for flexibility
      fileMap.set(nodePath, node.content)
      fileMap.set(node.path, node.content)
      // Also store just the relative path from root
      const relativePath = node.path.split('/').slice(1).join('/')
      fileMap.set(relativePath, node.content)
    }
    if (node.children) {
      node.children.forEach(child => traverse(child, nodePath))
    }
  }

  traverse(root)

  return (path: string) => {
    // Try exact match first
    if (fileMap.has(path)) return fileMap.get(path)
    // Try without leading slash
    if (fileMap.has(path.replace(/^\//, ''))) return fileMap.get(path.replace(/^\//, ''))
    // Try just the filename
    const fileName = path.split('/').pop() || ''
    for (const [key, value] of fileMap.entries()) {
      if (key.endsWith('/' + fileName) || key === fileName) {
        return value
      }
    }
    return undefined
  }
}
