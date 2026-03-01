import { useState, useCallback, useMemo } from 'react'
import { Header } from './components/Header'
import { FolderUploader } from './components/FolderUploader'
import { FileTree } from './components/FileTree'
import { JsonEditor } from './components/JsonEditor'
import { JsonTreeView } from './components/JsonTreeView'
import { LauncherPanel } from './components/Launcher'
import { ConsultationDashboard } from './components/ConsultationDashboard'
import { useFileSystem } from './hooks/useFileSystem'
import './App.css'

type ViewMode = 'editor' | 'tree'
type Tab = 'launch' | 'monitor'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('launch')
  const [viewMode, setViewMode] = useState<ViewMode>('editor')
  const [showLauncher, setShowLauncher] = useState(false)
  const {
    root,
    selectedFile,
    error,
    loadDirectory,
    selectFile,
    updateFileContent,
    clearFileSystem,
    getModifiedFiles
  } = useFileSystem()

  const modifiedFiles = useMemo(() => getModifiedFiles(), [getModifiedFiles])

  const handleDownloadFile = useCallback(() => {
    if (!selectedFile || !selectedFile.content) return

    const blob = new Blob([selectedFile.content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = selectedFile.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [selectedFile])

  const handleDownloadAll = useCallback(async () => {
    if (!root) return

    // Dynamic import of JSZip
    const JSZip = (await import('jszip')).default
    const zip = new JSZip()

    const addToZip = (node: typeof root, currentZip: typeof zip) => {
      if (node.type === 'file' && node.content !== undefined) {
        // Remove the root folder name from the path
        const pathParts = node.path.split('/')
        const relativePath = pathParts.slice(1).join('/')
        currentZip.file(relativePath, node.content)
      }
      if (node.children) {
        node.children.forEach(child => addToZip(child, currentZip))
      }
    }

    addToZip(root, zip)

    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${root.name}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [root])

  const handleFormat = useCallback(() => {
    if (!selectedFile?.content || !selectedFile.name.endsWith('.json')) return

    try {
      const formatted = JSON.stringify(JSON.parse(selectedFile.content), null, 2)
      updateFileContent(selectedFile.path, formatted)
    } catch {
      // Invalid JSON, ignore
    }
  }, [selectedFile, updateFileContent])

  const handleContentChange = useCallback((content: string) => {
    if (selectedFile) {
      updateFileContent(selectedFile.path, content)
    }
  }, [selectedFile, updateFileContent])

  const handleLaunch = useCallback(() => {
    setShowLauncher(true)
  }, [])

  const handleCloseLauncher = useCallback(() => {
    setShowLauncher(false)
  }, [])

  const parsedJson = useMemo(() => {
    if (!selectedFile?.content || !selectedFile.name.endsWith('.json')) return null
    try {
      return JSON.parse(selectedFile.content) as object | unknown[]
    } catch {
      return null
    }
  }, [selectedFile])

  const getLanguage = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'json': return 'json'
      case 'js': return 'javascript'
      case 'ts': return 'typescript'
      case 'jsx': return 'javascript'
      case 'tsx': return 'typescript'
      case 'css': return 'css'
      case 'scss': return 'scss'
      case 'html': return 'html'
      case 'md': return 'markdown'
      case 'py': return 'python'
      case 'yaml':
      case 'yml': return 'yaml'
      case 'xml': return 'xml'
      case 'sh': return 'shell'
      case 'sql': return 'sql'
      default: return 'plaintext'
    }
  }

  return (
    <div className="app">
      {/* Tab Bar */}
      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'launch' ? 'active' : ''}`}
          onClick={() => setActiveTab('launch')}
        >
          Launch Panel
        </button>
        <button
          className={`tab-btn ${activeTab === 'monitor' ? 'active' : ''}`}
          onClick={() => setActiveTab('monitor')}
        >
          Monitor Panel
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        <div style={{ display: activeTab === 'launch' ? 'contents' : 'none' }}>
          <Header
            rootName={root?.name || null}
            selectedFile={selectedFile}
            modifiedCount={modifiedFiles.length}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            onDownloadFile={handleDownloadFile}
            onDownloadAll={handleDownloadAll}
            onFormat={handleFormat}
            onClear={clearFileSystem}
            onLaunch={handleLaunch}
          />
          <main className="main-content">
            {!root ? (
              <FolderUploader onFolderSelect={loadDirectory} />
            ) : (
              <div className="workspace">
                <FileTree
                  root={root}
                  selectedPath={selectedFile?.path || null}
                  onSelect={selectFile}
                />
                <div className="editor-panel">
                  {selectedFile ? (
                    <div className="editor-container">
                      {viewMode === 'editor' ? (
                        <JsonEditor
                          content={selectedFile.content || ''}
                          onChange={handleContentChange}
                          error={error}
                          language={getLanguage(selectedFile.name)}
                        />
                      ) : (
                        parsedJson && <JsonTreeView data={parsedJson} />
                      )}
                    </div>
                  ) : (
                    <div className="no-file-selected">
                      <p>Select a file from the tree to edit</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>

          {/* Launcher Modal */}
          {showLauncher && root && (
            <>
              <div className="launcher-overlay" onClick={handleCloseLauncher} />
              <LauncherPanel root={root} onClose={handleCloseLauncher} />
            </>
          )}
        </div>
        <div style={{ display: activeTab === 'monitor' ? 'contents' : 'none' }}>
          <ConsultationDashboard />
        </div>
      </div>
    </div>
  )
}

export default App
