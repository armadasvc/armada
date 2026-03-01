import { LaunchResult as LaunchResultType } from '../../types/launcher'
import './LaunchResult.css'

interface LaunchResultProps {
  result: LaunchResultType | null
}

export function LaunchResult({ result }: LaunchResultProps) {
  if (!result) return null

  return (
    <div className={`launch-result ${result.success ? 'success' : 'error'}`}>
      <div className="result-header">
        {result.success ? '✅ Success' : '❌ Error'}
      </div>
      <pre className="result-message">{result.message}</pre>
    </div>
  )
}
