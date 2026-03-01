import { useState, useCallback, useEffect } from 'react'

const STORAGE_KEY = 'armada-json-editor-content'
const FILENAME_KEY = 'armada-json-editor-filename'

type JsonValue = object | unknown[]

interface UseJsonFileReturn {
  content: string | null
  parsedContent: JsonValue | null
  fileName: string | null
  error: string | null
  isValid: boolean
  loadFile: (file: File) => void
  updateContent: (newContent: string) => void
  clearFile: () => void
}

export function useJsonFile(): UseJsonFileReturn {
  const [content, setContent] = useState<string | null>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved
  })
  const [fileName, setFileName] = useState<string | null>(() => {
    return localStorage.getItem(FILENAME_KEY)
  })
  const [parsedContent, setParsedContent] = useState<JsonValue | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isValid, setIsValid] = useState(true)

  useEffect(() => {
    if (content !== null) {
      try {
        const parsed = JSON.parse(content) as JsonValue
        setParsedContent(parsed)
        setError(null)
        setIsValid(true)
        localStorage.setItem(STORAGE_KEY, content)
      } catch (e) {
        setParsedContent(null)
        setError(e instanceof Error ? e.message : 'Invalid JSON')
        setIsValid(false)
      }
    } else {
      setParsedContent(null)
      setError(null)
      setIsValid(true)
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [content])

  useEffect(() => {
    if (fileName) {
      localStorage.setItem(FILENAME_KEY, fileName)
    } else {
      localStorage.removeItem(FILENAME_KEY)
    }
  }, [fileName])

  const loadFile = useCallback((file: File) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      try {
        JSON.parse(text)
        setContent(text)
        setFileName(file.name)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Invalid JSON file')
      }
    }
    reader.onerror = () => {
      setError('Failed to read file')
    }
    reader.readAsText(file)
  }, [])

  const updateContent = useCallback((newContent: string) => {
    setContent(newContent)
  }, [])

  const clearFile = useCallback(() => {
    setContent(null)
    setFileName(null)
    setParsedContent(null)
    setError(null)
    setIsValid(true)
  }, [])

  return {
    content,
    parsedContent,
    fileName,
    error,
    isValid,
    loadFile,
    updateContent,
    clearFile
  }
}
