import { useState, useCallback, useMemo, useEffect } from 'react'
import { FileNode } from './useFileSystem'
import {
  CertificateStatus,
  LaunchResult,
  FileMapping,
  DEFAULT_FILE_MAPPINGS
} from '../types/launcher'
import { API_BASE } from '../types/consultation'
import {
  findFileByName,
  getFilesByExtension,
  createFileContentGetter,
  bundleScript,
  processConfig,
  testSslConnection,
  openCertificateAcceptance,
  getCertificateAcceptanceMessage,
  isHttpsUrl,
  sendLaunchRequest
} from '../utils/launcher'

interface UseLauncherProps {
  root: FileNode
}

interface UseLauncherReturn {
  // Form state
  apiUrl: string
  setApiUrl: (url: string) => void
  selectedConfigTemplate: string
  setSelectedConfigTemplate: (path: string) => void
  selectedConfigTune: string
  setSelectedConfigTune: (path: string) => void
  selectedDataJob: string
  setSelectedDataJob: (path: string) => void
  selectedDataAgent: string
  setSelectedDataAgent: (path: string) => void
  selectedRequirements: string
  setSelectedRequirements: (path: string) => void
  // Status
  isLaunching: boolean
  result: LaunchResult | null
  certStatus: CertificateStatus

  // Computed
  jsonFiles: FileNode[]
  csvFiles: FileNode[]
  txtFiles: FileNode[]
  fileStatus: FileMapping
  missingFiles: string[]
  canLaunch: boolean

  // Actions
  handleLaunch: () => Promise<void>
}

export function useLauncher({ root }: UseLauncherProps): UseLauncherReturn {
  // Form state
  const [apiUrl, setApiUrl] = useState('/api/bot/start')
  const [selectedConfigTemplate, setSelectedConfigTemplate] = useState('')
  const [selectedConfigTune, setSelectedConfigTune] = useState('')
  const [selectedDataJob, setSelectedDataJob] = useState('')
  const [selectedDataAgent, setSelectedDataAgent] = useState('')
  const [selectedRequirements, setSelectedRequirements] = useState('')
  // Status state
  const [isLaunching, setIsLaunching] = useState(false)
  const [result, setResult] = useState<LaunchResult | null>(null)
  const [certStatus, setCertStatus] = useState<CertificateStatus>('unknown')

  // Get all JSON files for configTemplate and configTune selection
  const jsonFiles = useMemo(() => getFilesByExtension(root, '.json'), [root])

  // Get all CSV files for data_job and data_agent selection
  const csvFiles = useMemo(() => getFilesByExtension(root, '.csv'), [root])

  // Get all TXT files for requirements selection
  const txtFiles = useMemo(() => getFilesByExtension(root, '.txt'), [root])

  // Preset defaults when file lists become available
  useEffect(() => {
    if (selectedConfigTemplate === '' && jsonFiles.length > 0) {
      const defaultFile = jsonFiles.find(f => f.path.endsWith(DEFAULT_FILE_MAPPINGS.configTemplate))
      if (defaultFile) setSelectedConfigTemplate(defaultFile.path)
    }
  }, [jsonFiles, selectedConfigTemplate])

  useEffect(() => {
    if (selectedConfigTune === '' && jsonFiles.length > 0) {
      const defaultFile = jsonFiles.find(f => f.path.endsWith(DEFAULT_FILE_MAPPINGS.configTune))
      if (defaultFile) setSelectedConfigTune(defaultFile.path)
    }
  }, [jsonFiles, selectedConfigTune])

  useEffect(() => {
    if (selectedDataJob === '' && csvFiles.length > 0) {
      const defaultFile = csvFiles.find(f => f.path.endsWith(DEFAULT_FILE_MAPPINGS.dataJob))
      if (defaultFile) setSelectedDataJob(defaultFile.path)
    }
  }, [csvFiles, selectedDataJob])

  useEffect(() => {
    if (selectedDataAgent === '' && csvFiles.length > 0) {
      const defaultFile = csvFiles.find(f => f.path.endsWith(DEFAULT_FILE_MAPPINGS.dataAgent))
      if (defaultFile) setSelectedDataAgent(defaultFile.path)
    }
  }, [csvFiles, selectedDataAgent])

  useEffect(() => {
    if (selectedRequirements === '' && txtFiles.length > 0) {
      const defaultFile = txtFiles.find(f => f.path.endsWith(DEFAULT_FILE_MAPPINGS.requirementsTxt))
      if (defaultFile) setSelectedRequirements(defaultFile.path)
    }
  }, [txtFiles, selectedRequirements])

  // Find the selected configTemplate file
  const selectedConfigTemplateFile = useMemo(() => {
    if (!selectedConfigTemplate) return null
    return jsonFiles.find(f => f.path === selectedConfigTemplate) || null
  }, [jsonFiles, selectedConfigTemplate])

  // Find the selected configTune file
  const selectedConfigTuneFile = useMemo(() => {
    if (!selectedConfigTune) return null
    return jsonFiles.find(f => f.path === selectedConfigTune) || null
  }, [jsonFiles, selectedConfigTune])

  // Find the selected dataJob file
  const selectedDataJobFile = useMemo(() => {
    if (!selectedDataJob) return null
    return csvFiles.find(f => f.path === selectedDataJob) || null
  }, [csvFiles, selectedDataJob])

  // Find the selected dataAgent file
  const selectedDataAgentFile = useMemo(() => {
    if (!selectedDataAgent) return null
    return csvFiles.find(f => f.path === selectedDataAgent) || null
  }, [csvFiles, selectedDataAgent])

  // Find the selected requirements file
  const selectedRequirementsFile = useMemo(() => {
    if (!selectedRequirements) return null
    return txtFiles.find(f => f.path === selectedRequirements) || null
  }, [txtFiles, selectedRequirements])

  // Check which required files are present (content can be empty)
  const fileStatus = useMemo((): FileMapping => {
    return {
      configTemplate: (selectedConfigTemplateFile?.content !== undefined) ? selectedConfigTemplateFile.path : null,
      configTune: (selectedConfigTuneFile?.content !== undefined) ? selectedConfigTuneFile.path : null,
      dataJob: selectedDataJob || null,  // Just check if selected, content can be empty
      dataAgent: selectedDataAgent || null,  // Just check if selected, content can be empty
      requirementsTxt: selectedRequirements || null
    }
  }, [selectedConfigTemplateFile, selectedConfigTuneFile, selectedDataJob, selectedDataAgent, selectedRequirements])

  // List of missing files
  const missingFiles = useMemo(() => {
    const missing: string[] = []
    if (!fileStatus.configTemplate) missing.push('Config Template (JSON)')
    if (!fileStatus.configTune) missing.push('Config Tune (JSON)')
    if (!fileStatus.dataJob) missing.push('Data Job (CSV)')
    if (!fileStatus.dataAgent) missing.push('Data Agent (CSV)')
    return missing
  }, [fileStatus])

  // Can we launch?
  const canLaunch = useMemo(() => {
    return apiUrl.trim() !== '' && missingFiles.length === 0
  }, [apiUrl, missingFiles])

  // Handle launch
  const handleLaunch = useCallback(async () => {
    if (!canLaunch) return

    setIsLaunching(true)
    setResult(null)

    try {
      // First, test SSL connection if using HTTPS
      if (isHttpsUrl(apiUrl) && certStatus !== 'accepted') {
        const sslOk = await testSslConnection(apiUrl, setCertStatus)
        if (!sslOk) {
          openCertificateAcceptance(apiUrl)
          setResult({
            success: false,
            message: getCertificateAcceptanceMessage()
          })
          setIsLaunching(false)
          return
        }
      }

      // Get file contents
      const getFileContent = createFileContentGetter(root)

      // Validate required files have content (dataJob/dataAgent can be empty)
      const missingContent: string[] = []
      if (!selectedConfigTemplateFile?.content) missingContent.push('Config Template')
      if (!selectedConfigTuneFile?.content) missingContent.push('Config Tune')

      if (missingContent.length > 0) {
        throw new Error(`Missing file contents: ${missingContent.join(', ')}`)
      }

      // Use empty string as default for data files if not loaded
      const dataJobContent = selectedDataJobFile?.content ?? ''
      const dataAgentContent = selectedDataAgentFile?.content ?? ''

      // Find main.py script (always main.py)
      const scriptFile = findFileByName(root, 'main.py')
      if (!scriptFile?.content) {
        throw new Error('main.py not found or empty')
      }

      // Bundle script
      const scriptContent = bundleScript(
        scriptFile.content,
        scriptFile.path,
        getFileContent,
        root.name
      )

      // Process config
      const { config: finalConfig, runId } = processConfig(
        selectedConfigTemplateFile!.content!,
        selectedConfigTuneFile!.content!,
        scriptContent
      )

      // Parse configTune for the payload
      const configTune = JSON.parse(selectedConfigTuneFile!.content!) as Record<string, unknown>

      // Get optional requirements.txt content
      const requirementsTxtContent = selectedRequirementsFile?.content ?? ''

      // Send request
      const response = await sendLaunchRequest({
        url: apiUrl,
        configTemplate: finalConfig,
        configTune,
        dataJob: dataJobContent,
        dataAgent: dataAgentContent,
        requirementsTxt: requirementsTxtContent,
      })

      // Register run in tracking backend
      if (response.success) {
        const runDatetime = new Date().toISOString().slice(0, 19) + '.000'
        try {
          await fetch(`${API_BASE}/api/runs/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ run_uuid: runId, run_datetime: runDatetime }),
          })
        } catch (err) {
          console.error('Failed to register run in tracking:', err)
        }
      }

      setResult(response)
    } catch (error) {
      setResult({
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      setIsLaunching(false)
    }
  }, [canLaunch, root, selectedConfigTemplateFile, selectedConfigTuneFile, selectedDataJobFile, selectedDataAgentFile, selectedRequirementsFile, apiUrl, certStatus])

  return {
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
  }
}
