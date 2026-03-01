import { useState } from 'react'
import { FileNode } from '../hooks/useFileSystem'
import './FileTree.css'

interface FileTreeProps {
  root: FileNode
  selectedPath: string | null
  onSelect: (file: FileNode) => void
}

interface TreeNodeProps {
  node: FileNode
  depth: number
  selectedPath: string | null
  onSelect: (file: FileNode) => void
}

function TreeNode({ node, depth, selectedPath, onSelect }: TreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(depth < 2)

  const handleClick = () => {
    if (node.type === 'directory') {
      setIsExpanded(!isExpanded)
    } else {
      onSelect(node)
    }
  }

  const isSelected = node.path === selectedPath

  return (
    <div className="tree-node">
      <div
        className={`tree-item ${isSelected ? 'selected' : ''} ${node.modified ? 'modified' : ''}`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === 'directory' && (
          <span className={`folder-icon ${isExpanded ? 'expanded' : ''}`}>
            {isExpanded ? '▼' : '▶'}
          </span>
        )}
        <span className={`file-icon ${node.type}`}>
          {node.type === 'directory' ? '📁' : getFileIcon(node.name)}
        </span>
        <span className="file-name">{node.name}</span>
        {node.modified && <span className="modified-dot">●</span>}
      </div>
      {node.type === 'directory' && isExpanded && node.children && (
        <div className="tree-children">
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'json':
      return '📋'
    case 'js':
    case 'ts':
    case 'jsx':
    case 'tsx':
      return '📜'
    case 'css':
    case 'scss':
    case 'sass':
      return '🎨'
    case 'html':
      return '🌐'
    case 'md':
      return '📝'
    case 'py':
      return '🐍'
    case 'yaml':
    case 'yml':
      return '⚙️'
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
    case 'svg':
      return '🖼️'
    default:
      return '📄'
  }
}

export function FileTree({ root, selectedPath, onSelect }: FileTreeProps) {
  return (
    <div className="file-tree">
      <div className="file-tree-header">
        <span className="folder-icon">📂</span>
        <span className="root-name">{root.name}</span>
      </div>
      <div className="file-tree-content">
        {root.children?.map((child) => (
          <TreeNode
            key={child.path}
            node={child}
            depth={0}
            selectedPath={selectedPath}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  )
}
