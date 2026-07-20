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
  [key: string]: string | number | boolean | null | undefined | KpiDetailBottomItem[]
}

export type E02MainStatus = '整改中' | '待复查' | '待销项'
export type E02DeadlineStatus = '已逾期' | '正常'

export type E02DetailRow = KpiDetailBottomItem & {
  id: string
  rawId: number
  category: string
  name: string
  time: string
  level: string
  department: string
  deadline: string
  mainStatus: E02MainStatus
  overdue: boolean
  deadlineStatus: E02DeadlineStatus
  status?: string
}

export type E03DeadlineStatus = '已逾期' | '正常'
export type E03MainStatus = '未闭环' | '待整改' | '整改中'

export type E03DetailRow = KpiDetailBottomItem & {
  id: number
  name: string
  segment: string
  category: string
  time: string
  department: string
  deadline: string
  mainStatus: E03MainStatus
  overdue: boolean
  deadlineStatus: E03DeadlineStatus
  statusStageKnown: boolean
}

export type E04MonthlyEmission = {
  period: string
  monthlyEmission: number
  cumulativeEmission: number
}

export type E04MaterialDetail = KpiDetailBottomItem & {
  material: string
  activityValue: number
  activityUnit: string
  emissionFactor: number
  factorUnit: string
  emission: number
  factorName: string
  factorVersion: string
  factorSource: string
  dataNature: 'demo'
  verificationStatus: '待业务核验'
  evidenceStatus: string
  monthlyData?: { period: string; activityValue: number; emission: number }[]
}

export type E04SourceDetail = KpiDetailBottomItem & {
  sourceCode: 'diesel' | 'electricity' | 'material' | 'transport'
  source: string
  activityValue: number
  activityUnit: string
  emissionFactor: number | null
  factorUnit: string
  factorName: string
  emission: number
  share: number
  factorVersion: string
  factorSource: string
  dataNature: 'demo'
  verificationStatus: '待业务核验'
  evidenceStatus: string
  materialDetails?: E04MaterialDetail[]
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
  statusData?: { name: string; value: number }[]
  statisticsAsOf?: string
  monthlyData?: E04MonthlyEmission[]
  materialDetails?: E04MaterialDetail[]
  accountingBoundary?: string[]
  demoNotice?: string
  dataNature?: string
}
