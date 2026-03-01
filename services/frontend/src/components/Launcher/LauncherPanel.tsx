import { FileNode } from '../../hooks/useFileSystem'
import { useLauncher } from '../../hooks/useLauncher'
import { isHttpsUrl } from '../../utils/launcher'
import { CertificateStatus } from './CertificateStatus'
import { FileStatusList } from './FileStatusList'
import { LaunchResult } from './LaunchResult'
import './LauncherPanel.css'

interface LauncherPanelProps {
  root: FileNode
  onClose: () => void
}

export function LauncherPanel({ root, onClose }: LauncherPanelProps) {
  const {
    apiUrl,
    setApiUrl,
    selectedConfigTemplate,
    setSelectedConfigTemplate,
    selectedConfigTune,
    setSelectedConfigTune,
    selectedDataJob,
    setSelectedDataJob,
    selectedDataAgent,
    setSelectedDataAgent,
    selectedRequirements,
    setSelectedRequirements,
    isLaunching,
    result,
    certStatus,
    jsonFiles,
    csvFiles,
    txtFiles,
    fileStatus,
    missingFiles,
    canLaunch,
    handleLaunch
  } = useLauncher({ root })

  return (
    <div className="launcher-panel">
      <div className="launcher-header">
        <h2>Launch to Cluster</h2>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="launcher-content">
        {/* API URL */}
        <div className="launcher-section">
          <label className="launcher-label">API URL</label>
          <div className="url-input-group">
            <input
              type="text"
              className="launcher-input"
              placeholder="/api/bot/start"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
            />
            {apiUrl && isHttpsUrl(apiUrl) && (
              <button
                className="cert-btn"
                onClick={() => window.open(apiUrl, '_blank')}
                title="Open URL to accept self-signed certificate"
              >
                🔓 Accept Cert
              </button>
            )}
          </div>
          <CertificateStatus
            status={certStatus}
            visible={isHttpsUrl(apiUrl)}
          />
        </div>

        {/* Config Template Selection */}
        <div className="launcher-section">
          <label className="launcher-label">Config Template (JSON)</label>
          <select
            className="launcher-select"
            value={selectedConfigTemplate}
            onChange={(e) => setSelectedConfigTemplate(e.target.value)}
          >
            <option value="">-- Select a JSON config template --</option>
            {jsonFiles.map(file => (
              <option key={file.path} value={file.path}>
                {file.path}
              </option>
            ))}
          </select>
        </div>

        {/* Config Tune Selection */}
        <div className="launcher-section">
          <label className="launcher-label">Config Tune (JSON)</label>
          <select
            className="launcher-select"
            value={selectedConfigTune}
            onChange={(e) => setSelectedConfigTune(e.target.value)}
          >
            <option value="">-- Select a JSON config file --</option>
            {jsonFiles.map(file => (
              <option key={file.path} value={file.path}>
                {file.path}
              </option>
            ))}
          </select>
        </div>

        {/* Data Job Selection */}
        <div className="launcher-section">
          <label className="launcher-label">Data Job (CSV)</label>
          <select
            className="launcher-select"
            value={selectedDataJob}
            onChange={(e) => setSelectedDataJob(e.target.value)}
          >
            <option value="">-- Select a CSV file --</option>
            {csvFiles.map(file => (
              <option key={file.path} value={file.path}>
                {file.path}
              </option>
            ))}
          </select>
        </div>

        {/* Data Agent Selection */}
        <div className="launcher-section">
          <label className="launcher-label">Data Agent (CSV)</label>
          <select
            className="launcher-select"
            value={selectedDataAgent}
            onChange={(e) => setSelectedDataAgent(e.target.value)}
          >
            <option value="">-- Select a CSV file --</option>
            {csvFiles.map(file => (
              <option key={file.path} value={file.path}>
                {file.path}
              </option>
            ))}
          </select>
        </div>

        {/* Requirements Selection (optional) */}
        <div className="launcher-section">
          <label className="launcher-label">Requirements (TXT) - Optional</label>
          <select
            className="launcher-select"
            value={selectedRequirements}
            onChange={(e) => setSelectedRequirements(e.target.value)}
          >
            <option value="">-- None --</option>
            {txtFiles.map(file => (
              <option key={file.path} value={file.path}>
                {file.path}
              </option>
            ))}
          </select>
        </div>

        {/* File Status */}
        <div className="launcher-section">
          <label className="launcher-label">Required Files Status</label>
          <FileStatusList fileStatus={fileStatus} />
        </div>

        {/* Missing Files Warning */}
        {missingFiles.length > 0 && (
          <div className="launcher-warning">
            Missing: {missingFiles.join(', ')}
          </div>
        )}

        {/* Result */}
        <LaunchResult result={result} />
      </div>

      <div className="launcher-footer">
        <button className="launcher-btn cancel" onClick={onClose}>
          Cancel
        </button>
        <button
          className="launcher-btn launch"
          onClick={handleLaunch}
          disabled={!canLaunch || isLaunching}
        >
          {isLaunching ? 'Launching...' : 'Launch'}
        </button>
      </div>
    </div>
  )
}
