import { FileNode } from '../hooks/useFileSystem'
import './Header.css'

interface HeaderProps {
  rootName: string | null
  selectedFile: FileNode | null
  modifiedCount: number
  viewMode: 'editor' | 'tree'
  onViewModeChange: (mode: 'editor' | 'tree') => void
  onDownloadFile: () => void
  onDownloadAll: () => void
  onFormat: () => void
  onClear: () => void
  onLaunch: () => void
}

export function Header({
  rootName,
  selectedFile,
  modifiedCount,
  viewMode,
  onViewModeChange,
  onDownloadFile,
  onDownloadAll,
  onFormat,
  onClear,
  onLaunch
}: HeaderProps) {
  const isJsonFile = selectedFile?.name.endsWith('.json')

  return (
    <header className="header">
      <div className="header-left">
        {rootName && (
          <span className="folder-badge">
            {rootName}
            {modifiedCount > 0 && (
              <span className="modified-count">{modifiedCount} modified</span>
            )}
          </span>
        )}
        {selectedFile && (
          <span className="file-badge">
            {selectedFile.name}
            {selectedFile.modified && <span className="modified-indicator">●</span>}
          </span>
        )}
      </div>
      <div className="header-right">
        {selectedFile && (
          <>
            <div className="view-toggle">
              <button
                className={`toggle-btn ${viewMode === 'editor' ? 'active' : ''}`}
                onClick={() => onViewModeChange('editor')}
              >
                Editor
              </button>
              <button
                className={`toggle-btn ${viewMode === 'tree' ? 'active' : ''}`}
                onClick={() => onViewModeChange('tree')}
                disabled={!isJsonFile}
                title={!isJsonFile ? 'Tree view only available for JSON files' : ''}
              >
                Tree
              </button>
            </div>
            {isJsonFile && (
              <button className="btn" onClick={onFormat}>
                Format
              </button>
            )}
            <button className="btn" onClick={onDownloadFile}>
              Save File
            </button>
          </>
        )}
        {rootName && (
          <>
            <button className="btn btn-launch" onClick={onLaunch} title="Launch to cluster">
              Launch
            </button>
            <button className="btn" onClick={onDownloadAll} title="Download all files as ZIP">
              Download All
            </button>
            <button className="btn btn-danger" onClick={onClear}>
              Close
            </button>
          </>
        )}
      </div>
    </header>
  )
}
