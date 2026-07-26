export interface E02SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

export interface E02IssueOverview {
  total: number
  rectifying: number
  pendingReview: number
  pendingClosure: number
  overdueAmong: number
}

export interface E02IssueItem {
  id: number
  businessCode: string
  title: string
  issueType: string
  locationText: string
  status: string
  statusGroup: 'rectifying' | 'pendingReview' | 'pendingClosure' | 'terminal'
  overdue: boolean
  deadline: string | null
  responsibleOrgName: string
  canLocate: boolean
  spatialLinks: E02SpatialLink[]
}

export interface E02HistoryItem {
  fromStatus: string | null
  toStatus: string
  actionCode: string | null
  actionAt: string | null
  operatorName: string
  operatorOrgName: string
  comment: string
  transitionResult: string
}

export interface E02PartyItem {
  role: string
  roleLabel: string
  orgName: string
  userName: string
}

export interface E02EvidenceItem {
  role: string
  roleLabel: string
  kind: string
  title: string
  description: string
  validityStatus: string
  createdAt: string | null
}

export interface E02MaterialCompleteness {
  requiredRoles: string[]
  coveredRoles: string[]
  pendingRoles: string[]
  ratio: string
  notes: string[]
}

export interface E02CaseInfo {
  caseId: number | null
  caseCode: string | null
  caseStatus: string | null
  caseStatusGroup: string | null
  openedAt: string | null
  closedAt: string | null
}

export interface E02IssueDetail {
  id: number
  businessCode: string
  title: string
  issueType: string
  locationText: string
  status: string
  statusGroup: string
  overdue: boolean
  deadline: string | null
  responsibleOrgName: string
  foundDate: string | null
  closedDate: string | null
  isDemo: boolean
  dataNature: string
  case: E02CaseInfo | null
  history: E02HistoryItem[]
  parties: E02PartyItem[]
  evidence: E02EvidenceItem[]
  materialCompleteness: E02MaterialCompleteness
  spatialLinks: E02SpatialLink[]
}

export interface E02IssuesPayload {
  overview: E02IssueOverview
  issues: E02IssueItem[]
  spatialLinks: E02SpatialLink[]
  scope: string
  isDemo: boolean
}

export type E02CategoryFilter = 'ALL' | 'RECTIFYING' | 'PENDING_REVIEW' | 'PENDING_CLOSURE'

export type E02PanelLayer = 'overview' | 'detail'
