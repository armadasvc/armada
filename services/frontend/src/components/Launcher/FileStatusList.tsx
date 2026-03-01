import { FileMapping } from '../../types/launcher'
import './FileStatusList.css'

interface FileStatusListProps {
  fileStatus: FileMapping
}

interface FileStatusItemProps {
  name: string
  mapped: string
  found: boolean
}

function FileStatusItem({ name, mapped, found }: FileStatusItemProps) {
  return (
    <div className={`file-status-item ${found ? 'found' : 'missing'}`}>
      <span className="status-icon">{found ? '✓' : '✗'}</span>
      <span className="file-name">{name}</span>
      <span className="file-mapping">→ {mapped}</span>
    </div>
  )
}

function getFileName(path: string | null): string {
  if (!path) return '(not selected)'
  const parts = path.split('/')
  return parts[parts.length - 1]
}

export function FileStatusList({ fileStatus }: FileStatusListProps) {
  const files = [
    {
      name: fileStatus.configTemplate ? getFileName(fileStatus.configTemplate) : '(select config template)',
      mapped: 'configtemplate',
      found: !!fileStatus.configTemplate
    },
    {
      name: fileStatus.configTune ? getFileName(fileStatus.configTune) : '(select config tune)',
      mapped: 'configtune',
      found: !!fileStatus.configTune
    },
    {
      name: fileStatus.dataJob ? getFileName(fileStatus.dataJob) : '(select data job)',
      mapped: 'data_job',
      found: !!fileStatus.dataJob
    },
    {
      name: fileStatus.dataAgent ? getFileName(fileStatus.dataAgent) : '(select data agent)',
      mapped: 'data_agent',
      found: !!fileStatus.dataAgent
    },
    {
      name: fileStatus.requirementsTxt ? getFileName(fileStatus.requirementsTxt) : '(none)',
      mapped: 'requirements_txt (optional)',
      found: !!fileStatus.requirementsTxt
    }
  ]

  return (
    <div className="file-status-list">
      {files.map((file, index) => (
        <FileStatusItem
          key={`${file.mapped}-${index}`}
          name={file.name}
          mapped={file.mapped}
          found={file.found}
        />
      ))}
    </div>
  )
}
