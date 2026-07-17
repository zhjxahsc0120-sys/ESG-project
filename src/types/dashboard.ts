export type NavItem = {
  key: string
  label: string
  active?: boolean
}

export type KpiKey =
  | 'E01' | 'E02' | 'E03' | 'E04'
  | 'S01' | 'S02' | 'S03' | 'S04'
  | 'G01' | 'G02' | 'G03' | 'G04'

export type KpiTheme = 'green' | 'blue' | 'purple'

export type KpiItem = {
  key: KpiKey
  label: string
  fullName: string
  value: string | number
  unit?: string
}

export type KpiGroup = {
  key: 'E' | 'S' | 'G'
  title: string
  theme: KpiTheme
  status: string
  items: KpiItem[]
}

export type RoutePointType = 'compliance' | 'carbon' | 'risk' | 'sensitive' | 'station'

export type RoutePoint = {
  id: string
  name: string
  x: number
  y: number
  type: RoutePointType
}

export type RouteSegment = {
  id: string
  name: string
  points: [number, number][]
  status: 'normal' | 'warning' | 'risk'
}

export type SensitiveArea = {
  id: string
  name: string
  polygon: [number, number][]
}

export type ComplianceMetric = {
  label: string
  value: number
  unit: string
}

export type EffectivenessItem = {
  label: string
  value: number
}

export type CarbonSource = {
  name: string
  value: number
  color?: string
}

export type ReductionMeasure = {
  name: string
  level: string
}

export type MonthlyMaterial = {
  name: string
  owner: string
  deadline: string
}

export type MonthlyReport = {
  month: string
  progress: number
  pendingCount: number
  confirmCount: number
  currentStatus?: string
  expectedCompletion?: string
  materials: MonthlyMaterial[]
}

export type TimelineStep = {
  index: number
  label: string
  active?: boolean
  completed?: boolean
}

export interface KpiModalFocusContext {
  sourceTable?: string
  sourceId?: string
  gisFeatureId?: string
  from?: 'gis' | 'dashboard' | 'workspace'
  title?: string
}

// ── 弹窗详情类型 ──

export type KpiDetailSummaryItem = {
  label: string
  value: string | number
  unit?: string
  icon?: string
  extra?: string
}

export type KpiDetailBottomItem = {
  [key: string]: string | number
}

export type TopicTab = {
  key: string
  label: string
}

export type KpiDetailConfig = {
  key: KpiKey | string
  fullName: string
  theme: KpiTheme
  summary: KpiDetailSummaryItem[]
  chartTitle: string
  detailTitle: string
  detailColumns: { key: string; label: string; width?: string }[]
  detailData: KpiDetailBottomItem[]
  dataSource: string
  updateTime: string
  updateFrequency: string
  completeness: string
  completenessStatus: 'complete' | 'incomplete' | 'pending'
  isMock: boolean
  detailReserved?: boolean
  canSupervise?: boolean
  isTopic?: boolean
  tabs?: TopicTab[]
  topicData?: Record<string, any>
  categoryData?: { name: string; value: number }[]
}
