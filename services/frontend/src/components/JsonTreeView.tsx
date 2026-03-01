import { JsonView, defaultStyles } from 'react-json-view-lite'
import 'react-json-view-lite/dist/index.css'
import './JsonTreeView.css'

interface JsonTreeViewProps {
  data: object | unknown[]
}

const customStyles = {
  ...defaultStyles,
  container: 'json-tree-container',
  basicChildStyle: 'json-tree-child',
  label: 'json-tree-label',
  nullValue: 'json-tree-null',
  undefinedValue: 'json-tree-undefined',
  stringValue: 'json-tree-string',
  booleanValue: 'json-tree-boolean',
  numberValue: 'json-tree-number',
  otherValue: 'json-tree-other',
  punctuation: 'json-tree-punctuation',
  expandIcon: 'json-tree-expand',
  collapseIcon: 'json-tree-collapse',
  collapsedContent: 'json-tree-collapsed'
}

export function JsonTreeView({ data }: JsonTreeViewProps) {
  return (
    <div className="json-tree-wrapper">
      <JsonView
        data={data}
        shouldExpandNode={(level) => level < 2}
        style={customStyles}
      />
    </div>
  )
}
