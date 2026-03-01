import Editor from '@monaco-editor/react'
import './JsonEditor.css'

interface JsonEditorProps {
  content: string
  onChange: (value: string) => void
  error: string | null
  language?: string
}

export function JsonEditor({ content, onChange, error, language = 'json' }: JsonEditorProps) {
  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  return (
    <div className="json-editor">
      <Editor
        height="100%"
        language={language}
        value={content}
        onChange={handleEditorChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
          folding: true,
          formatOnPaste: true
        }}
      />
      {error && (
        <div className="editor-error">
          <span className="error-icon">!</span>
          {error}
        </div>
      )}
    </div>
  )
}
