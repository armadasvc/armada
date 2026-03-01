import { useState, useCallback } from 'react'

export interface FileNode {
  name: string
  path: string
  type: 'file' | 'directory'
  content?: string
  children?: FileNode[]
  modified?: boolean
}

interface UseFileSystemReturn {
  root: FileNode | null
  selectedFile: FileNode | null
  error: string | null
  loadDirectory: (files: FileList) => void
  selectFile: (file: FileNode) => void
  updateFileContent: (path: string, content: string) => void
  clearFileSystem: () => void
  getModifiedFiles: () => FileNode[]
}

function buildFileTree(files: FileList): FileNode {
  const root: FileNode = {
    name: '',
    path: '',
    type: 'directory',
    children: []
  }

  // Get the root folder name from the first file's path
  const firstPath = files[0]?.webkitRelativePath || ''
  const rootName = firstPath.split('/')[0] || 'root'
  root.name = rootName

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const relativePath = file.webkitRelativePath || file.name
    const parts = relativePath.split('/')

    // Skip the root folder name
    const pathParts = parts.slice(1)

    let current = root
    for (let j = 0; j < pathParts.length; j++) {
      const part = pathParts[j]
      const isFile = j === pathParts.length - 1
      const currentPath = parts.slice(0, j + 2).join('/')

      if (isFile) {
        current.children = current.children || []
        current.children.push({
          name: part,
          path: currentPath,
          type: 'file',
          content: undefined // Will be loaded on demand
        })
      } else {
        current.children = current.children || []
        let child = current.children.find(c => c.name === part && c.type === 'directory')
        if (!child) {
          child = {
            name: part,
            path: currentPath,
            type: 'directory',
            children: []
          }
          current.children.push(child)
        }
        current = child
      }
    }
  }

  // Sort children: directories first, then alphabetically
  const sortChildren = (node: FileNode) => {
    if (node.children) {
      node.children.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      })
      node.children.forEach(sortChildren)
    }
  }
  sortChildren(root)

  return root
}

function updateFileInTree(root: FileNode, path: string, content: string): FileNode {
  if (root.path === path) {
    return { ...root, content, modified: true }
  }
  if (root.children) {
    return {
      ...root,
      children: root.children.map(child => updateFileInTree(child, path, content))
    }
  }
  return root
}

function collectModifiedFiles(node: FileNode, files: FileNode[] = []): FileNode[] {
  if (node.type === 'file' && node.modified) {
    files.push(node)
  }
  if (node.children) {
    node.children.forEach(child => collectModifiedFiles(child, files))
  }
  return files
}

export function useFileSystem(): UseFileSystemReturn {
  const [root, setRoot] = useState<FileNode | null>(null)
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadDirectory = useCallback((files: FileList) => {
    if (files.length === 0) return

    const tree = buildFileTree(files)
    setRoot(tree)
    setSelectedFile(null)
    setError(null)

    // Load all file contents
    const contents = new Map<string, string>()
    let loaded = 0
    const totalFiles = Array.from(files).length

    Array.from(files).forEach(file => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        const filePath = file.webkitRelativePath || file.name
        contents.set(filePath, text)
        loaded++

        if (loaded === totalFiles) {
          // Update tree with contents
          setRoot(prevRoot => {
            if (!prevRoot) return prevRoot
            const updateContents = (node: FileNode): FileNode => {
              if (node.type === 'file') {
                // Try multiple path variations to find content
                const content = contents.get(node.path)
                  || contents.get(node.name)
                  || Array.from(contents.entries()).find(([k]) => k.endsWith('/' + node.name))?.[1]
                return { ...node, content }
              }
              if (node.children) {
                return { ...node, children: node.children.map(updateContents) }
              }
              return node
            }
            return updateContents(prevRoot)
          })
        }
      }
      reader.onerror = () => {
        setError(`Failed to read file: ${file.name}`)
      }
      reader.readAsText(file)
    })
  }, [])

  const selectFile = useCallback((file: FileNode) => {
    if (file.type === 'file') {
      setSelectedFile(file)
    }
  }, [])

  const updateFileContent = useCallback((path: string, content: string) => {
    setRoot(prevRoot => {
      if (!prevRoot) return prevRoot
      const updated = updateFileInTree(prevRoot, path, content)
      // Update selected file if it's the one being edited
      setSelectedFile(prev => {
        if (prev && prev.path === path) {
          return { ...prev, content, modified: true }
        }
        return prev
      })
      return updated
    })
  }, [])

  const clearFileSystem = useCallback(() => {
    setRoot(null)
    setSelectedFile(null)
    setError(null)
  }, [])

  const getModifiedFiles = useCallback(() => {
    if (!root) return []
    return collectModifiedFiles(root)
  }, [root])

  return {
    root,
    selectedFile,
    error,
    loadDirectory,
    selectFile,
    updateFileContent,
    clearFileSystem,
    getModifiedFiles
  }
}
