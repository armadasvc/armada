import { useCallback, useState, useRef } from 'react'
import './FolderUploader.css'

interface FolderUploaderProps {
  onFolderSelect: (files: FileList) => void
}

export function FolderUploader({ onFolderSelect }: FolderUploaderProps) {
  const [isDragging, setIsDragging] = useState(false)
  const folderInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const items = e.dataTransfer.items
    if (items.length > 0) {
      const item = items[0]
      const entry = item.webkitGetAsEntry()
      if (entry?.isDirectory) {
        const files = await readDirectory(entry as FileSystemDirectoryEntry)
        const dataTransfer = new DataTransfer()
        files.forEach(f => dataTransfer.items.add(f))
        onFolderSelect(dataTransfer.files)
      }
    }
  }, [onFolderSelect])

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      onFolderSelect(files)
    }
  }

  const handleClick = () => {
    folderInputRef.current?.click()
  }

  return (
    <div
      className={`folder-uploader ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={folderInputRef}
        type="file"
        // @ts-expect-error webkitdirectory is not in types
        webkitdirectory=""
        directory=""
        multiple
        onChange={handleFolderChange}
        style={{ display: 'none' }}
      />
      <div className="upload-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          <line x1="12" y1="11" x2="12" y2="17" />
          <polyline points="9 14 12 11 15 14" />
        </svg>
      </div>
      <p className="upload-text">
        Drag & drop a folder here, or click to select
      </p>
      <p className="upload-hint">
        Navigate and edit files within the folder
      </p>
    </div>
  )
}

async function readDirectory(dirEntry: FileSystemDirectoryEntry): Promise<File[]> {
  const files: File[] = []

  async function readEntries(entry: FileSystemDirectoryEntry, path: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const reader = entry.createReader()
      const readBatch = () => {
        reader.readEntries(async (entries) => {
          if (entries.length === 0) {
            resolve()
            return
          }

          for (const e of entries) {
            if (e.isFile) {
              const file = await getFile(e as FileSystemFileEntry, path)
              files.push(file)
            } else if (e.isDirectory) {
              await readEntries(e as FileSystemDirectoryEntry, `${path}/${e.name}`)
            }
          }

          readBatch()
        }, reject)
      }
      readBatch()
    })
  }

  await readEntries(dirEntry, dirEntry.name)
  return files
}

function getFile(fileEntry: FileSystemFileEntry, path: string): Promise<File> {
  return new Promise((resolve, reject) => {
    fileEntry.file((file) => {
      // Create a new file with the relative path
      const newFile = new File([file], file.name, { type: file.type })
      Object.defineProperty(newFile, 'webkitRelativePath', {
        value: `${path}/${file.name}`,
        writable: false
      })
      resolve(newFile)
    }, reject)
  })
}
