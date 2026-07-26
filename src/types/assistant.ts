export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: string
  kpiCards?: AssistantKpiCard[]
  tableData?: AssistantTableData
  dataBasis?: AssistantDataBasis
  followUps?: string[]
  loading?: boolean
}

export interface AssistantKpiCard {
  label: string
  value: string | number
  unit?: string
  color?: 'green' | 'blue' | 'purple' | 'orange' | 'red' | 'cyan'
}

export interface AssistantTableColumn {
  key: string
  label: string
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface AssistantTableData {
  title: string
  total?: number
  columns: AssistantTableColumn[]
  rows: Record<string, string | number>[]
  viewAllText?: string
}

export interface AssistantDataBasis {
  itemName: string
  scope: string
  updateTime: string
  dataPeriod: string
  verifyStatus: string
  stableId: string
  sources: Array<{
    name: string
    time: string
    status: string
  }>
  caliber: string
}

export interface ChatSession {
  id: string
  title: string
  lastTime: string
  active?: boolean
}

export interface QuickCategory {
  key: string
  name: string
  desc: string
  color: string
  icon: string
}
