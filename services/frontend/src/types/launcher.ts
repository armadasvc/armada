import { FileNode } from '../hooks/useFileSystem'

export interface LaunchConfig {
  apiUrl: string
}

export interface LaunchPayload {
  url: string
  configTemplate: Record<string, unknown>
  configTune: Record<string, unknown>
  dataJob: string
  dataAgent: string
  requirementsTxt?: string
}

export interface LaunchResult {
  success: boolean
  message: string
}

export interface RequiredFiles {
  configTemplate: FileNode | null
  configTune: FileNode | null
  dataJob: FileNode | null
  dataAgent: FileNode | null
}

export interface FileMapping {
  configTemplate: string | null
  configTune: string | null
  dataJob: string | null
  dataAgent: string | null
  requirementsTxt: string | null
}

export type CertificateStatus = 'unknown' | 'checking' | 'accepted' | 'pending'

export const DEFAULT_FILE_MAPPINGS = {
  configTemplate: 'config/config_template.json',
  configTune: 'config/config_distant.json',
  dataJob: 'config/data_job.csv',
  dataAgent: 'config/data_agent.csv',
  requirementsTxt: 'requirements.txt'
} as const
