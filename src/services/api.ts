import type { KpiDetailConfig, KpiGroup } from '@/types/dashboard'
import type { MonthlyReadiness, MonthlyReportOverview } from '@/types/monthly-report'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765'

export async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export async function apiHealth(): Promise<{ ok: boolean; service: string; db: string } | null> {
  return apiGet('/health')
}

export async function getDashboardKpis(): Promise<{ groups: KpiGroup[] } | null> {
  return apiGet('/api/dashboard/kpis')
}

export async function getDashboardKpiS01(): Promise<S01Data | null> {
  return apiGet('/api/dashboard/kpi/S01')
}

export async function getDashboardKpiDetail(key: string): Promise<KpiDetailConfig | null> {
  return apiGet(`/api/dashboard/kpi/${key}`)
}

export async function getDashboardTopic(topic: 'carbon' | 'monthly-report'): Promise<KpiDetailConfig | null> {
  return apiGet(topic === 'carbon' ? '/api/carbon/benefit-overview' : `/api/dashboard/topics/${topic}`)
}

export async function getDashboardPanels(): Promise<DashboardPanels | null> {
  return apiGet('/api/dashboard/panels')
}

export async function getMonthlyReportReadiness(reportPeriod: string): Promise<MonthlyReadiness | null> {
  const params = new URLSearchParams({ reportPeriod })
  return apiGet<MonthlyReadiness>(`/api/monthly-report/readiness?${params.toString()}`)
}

// Codex 已完成的新版月报概览接口：MySQL → 服务端 JSON 契约快照 → 前端 Mock
export async function getMonthlyReportOverview(reportMonth: string): Promise<MonthlyReportOverview | null> {
  const params = new URLSearchParams({ reportMonth })
  return apiGet<MonthlyReportOverview>(`/api/monthly/report-overview?${params.toString()}`)
}

export async function getWorkspaceSummary(): Promise<WorkspaceSummary | null> {
  return apiGet('/api/workspace/summary')
}

export async function getWorkspaceTasks(params?: {
  module?: string
  status?: string
  keyword?: string
  cycle?: string
  cycleType?: string
  deadlineStart?: string
  deadlineEnd?: string
  assignee?: string
}): Promise<{ total: number; items: UploadTask[] } | null> {
  const qs = new URLSearchParams()
  if (params?.module) qs.set('module', params.module)
  if (params?.status) qs.set('status', params.status)
  if (params?.keyword) qs.set('keyword', params.keyword)
  if (params?.cycle) qs.set('cycle', params.cycle)
  if (params?.cycleType) qs.set('cycleType', params.cycleType)
  if (params?.deadlineStart) qs.set('deadlineStart', params.deadlineStart)
  if (params?.deadlineEnd) qs.set('deadlineEnd', params.deadlineEnd)
  if (params?.assignee) qs.set('assignee', params.assignee)
  const query = qs.toString()
  return apiGet(`/api/workspace/tasks${query ? `?${query}` : ''}`)
}

export async function getDocumentsSummary(): Promise<DocumentsSummary | null> {
  return apiGet('/api/workspace/documents/summary')
}

export async function getDocuments(): Promise<{ total: number; items: DocumentItem[] } | null> {
  return apiGet('/api/workspace/documents')
}

export async function getDocumentDetail(documentId: string | number): Promise<DocumentDetailApi | null> {
  return apiGet(`/api/workspace/documents/${documentId}`)
}

export async function getDocumentVersions(documentId: string | number): Promise<{ items: DocumentVersionApi[] } | null> {
  return apiGet(`/api/workspace/documents/${documentId}/versions`)
}

export async function getDocumentRelations(documentId: string | number): Promise<{ items: DocumentRelationApi[] } | null> {
  return apiGet(`/api/workspace/documents/${documentId}/relations`)
}

export async function getReviews(): Promise<{ statusCards: StatusCard[]; items: ReviewItem[] } | null> {
  return apiGet('/api/workspace/reviews')
}

export async function getTaskDetail(taskId: string): Promise<TaskDetailApi | null> {
  return apiGet(`/api/workspace/tasks/${taskId}/detail`)
}

export async function saveTaskDraft(taskId: string, payload?: {
  comment?: string
  operatorId?: number
  operatorName?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/save`, payload || {})
}

export async function linkTaskDocument(taskId: string, payload: {
  documentId: string | number
  requirementId?: string
  matchScore?: number
  operatorId?: number
  source?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/link-document`, payload)
}

export async function submitTaskReview(taskId: string, payload?: {
  comment?: string
  operatorId?: number
  operatorName?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/submit`, payload || {})
}

export async function getReviewDetail(reviewId: string | number): Promise<ReviewDetailApi | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}`)
}

export async function getReviewTimeline(reviewId: string | number): Promise<{ items: ReviewTimelineApi[] } | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}/timeline`)
}

export async function getReviewRequirements(reviewId: string | number): Promise<{ items: ReviewRequirementApi[] } | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}/requirements`)
}

export async function approveReview(reviewId: string | number, payload?: {
  reviewer?: string
  operatorName?: string
  comment?: string
}): Promise<ReviewActionResponse | null> {
  return apiPost(`/api/workspace/reviews/${reviewId}/approve`, payload || {})
}

export async function returnReview(reviewId: string | number, payload?: {
  reviewer?: string
  operatorName?: string
  comment?: string
  requirements?: string[]
}): Promise<ReviewActionResponse | null> {
  return apiPost(`/api/workspace/reviews/${reviewId}/return`, payload || {})
}

export async function getParseQueue(): Promise<{ items: ParseQueueItem[] } | null> {
  return apiGet('/api/workspace/ai/parse-queue')
}

export async function uploadWorkspaceFile(payload: {
  originalName: string
  fileSize: number
  mimeType?: string
  uploaderId?: number
  uploaderName?: string
}): Promise<UploadFileResponse | null> {
  return apiPost('/api/workspace/files/upload', payload)
}

export async function uploadWorkspaceBinaryFile(file: File, meta?: {
  uploaderId?: number
  uploaderName?: string
}): Promise<UploadFileResponse | null> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (meta?.uploaderId) formData.append('uploaderId', String(meta.uploaderId))
    if (meta?.uploaderName) formData.append('uploaderName', meta.uploaderName)
    const res = await fetch(`${API_BASE}/api/workspace/files/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) return null
    return (await res.json()) as UploadFileResponse
  } catch {
    return null
  }
}

export async function startParseFile(fileId: number): Promise<ParseJobResponse | null> {
  return apiPost(`/api/workspace/files/${fileId}/parse`, {})
}

export async function getParseJob(jobId: number): Promise<ParseJobDetail | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}`)
}

export async function getParseFields(jobId: number): Promise<{ items: ParseFieldItem[] } | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}/fields`)
}

export async function getMatchCandidates(jobId: number): Promise<{ items: MatchCandidateItem[] } | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}/match-candidates`)
}

export async function confirmParseJob(
  jobId: number,
  payload: {
    confirmedFields: { fieldKey: string; confirmedValue: string }[]
    acceptedCandidateIds: number[]
    operatorId?: number
    operatorName?: string
    comment?: string
  }
): Promise<ConfirmParseResponse | null> {
  return apiPost(`/api/workspace/parse-jobs/${jobId}/confirm`, payload)
}

async function apiPost<T>(path: string, payload: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

type S01Data = {
  projectStartDate: string
  currentDate: string
  continuousDays: number
  currentStage: string
  currentStageDetail: string
  countingStatus: string
  latestInterruptDate?: string
  latestInterruptReason?: string
  updateTime: string
  timeline: {
    startLabel: string
    startDate: string
    message: string
    endLabel: string
    endDate: string
    months: string[]
  }
  constructionStages: {
    id: string
    name: string
    status: string
    detail?: string
    startDate?: string
    endDate?: string
  }[]
  conclusion: string
}

type DashboardPanels = {
  compliance?: {
    metrics?: unknown[]
    effectiveness?: unknown[]
    safeguards?: string[]
  }
  carbon?: {
    metrics?: unknown[]
    sources?: unknown[]
    reductions?: unknown[]
  }
  monthly?: unknown
  timeline?: unknown[]
  gis?: {
    routePoints?: unknown[]
    routeSegments?: unknown[]
    sensitiveAreas?: unknown[]
  }
}

type WorkspaceSummary = {
  currentTodo: number
  pendingUpload: number
  pendingCorrection: number
  pendingSubmit: number
  underReview: number
  dueSoon: number
  completed: number
}

type UploadTask = {
  id: string
  name: string
  module: string
  moduleName: string
  cycle: string
  cycleType: string
  deadline: string
  deadlineDisplay: string
  progressCurrent: number
  progressTotal: number
  status: string
  nextStep: string
  assignee: string
  assigneeDept: string
  priorityCode: string
}

type DocumentsSummary = {
  documentTotal: number
  monthNew: number
  pendingArchive: number
  expiringSoon: number
}

type DocumentItem = {
  id: string
  documentName: string
  documentType: string
  module: string
  period: string
  version: string
  source: string
  relationCount: number
  validityStatus: string
  uploadedAt: string
}

type StatusCard = {
  label: string
  value: number
  unit: string
  color: string
}

type ReviewItem = {
  id: string
  taskId?: string
  taskName: string
  module: string
  moduleName: string
  submitTime: string
  status: string
  reviewer: string
  commentSummary: string
  nextStep: string
}

type ParseQueueItem = {
  id: string
  jobId?: number
  fileId?: number
  fileName: string
  size: string
  progress: number
  status: string
}

export type UploadFileResponse = {
  fileId: number
  fileCode: string
  originalName: string
  fileSize?: number
  storagePath?: string
  sha256Hash: string
  duplicateStatus: string
  matchedFileId?: number | null
  matchedDocumentId?: number | null
  parseStatus: string
}

export type ParseJobResponse = {
  jobId: number
  jobCode: string
  jobStatus: string
}

export type ParseJobDetail = {
  jobId: number
  jobCode: string
  fileId: number
  fileName: string
  jobStatus: string
  confidence: number
  startedAt: string
  finishedAt: string
}

export type ParseFieldItem = {
  id: number
  fieldKey: string
  fieldName: string
  fieldValue: string
  normalizedValue: string
  valueType: string
  confidence: number
  confirmStatus: string
  confirmedValue: string | null
}

export type MatchCandidateItem = {
  candidateId: number
  taskId: string
  taskName: string
  module: string
  matchScore: number
  matchReason: string
  reuseCount: number
  candidateStatus: string
}

export type ConfirmParseResponse = {
  documentId: number
  documentCode: string
  documentStatus: string
  linkedTaskCount: number
  linkedTasks?: {
    taskId: string
    taskName: string
    requirementId: string | null
    requirementName: string | null
    progress: {
      completed: number
      total: number
      missing: number
      abnormal: number
      canSubmit: boolean
    }
  }[]
}

export type DocumentDetailApi = {
  id: string
  documentCode: string
  documentName: string
  documentType: string
  module: string
  period: string
  version: string
  source: string
  relationCount: number
  validityStatus: string
  documentStatus: string
  confirmStatus: string
  responsibleUnit: string
  validStartDate: string | null
  validEndDate: string | null
  uploadedAt: string
  file: {
    fileId: number | null
    originalName: string
    fileExt: string | null
    mimeType: string | null
    fileSize: number | null
    fileSizeText: string
    sha256Hash: string | null
    uploadSource: string | null
    uploadTime: string | null
  }
  tags: string[]
  isUnique: boolean
}

export type DocumentVersionApi = {
  id: number | string
  documentId: string
  fileId?: number
  versionNo: string
  versionDesc: string
  changeType: string
  uploadedBy?: number
  uploadedByName: string
  uploadedAt: string
  isCurrent: boolean
}

export type DocumentRelationApi = {
  id: number | string
  documentId: string
  taskId: string
  taskName: string
  module: 'E' | 'S' | 'G'
  moduleName: string
  cycle: string
  status: string
  relationType: string
  relationStatus: string
  matchScore: number
  source: string
  referenceCount: number
  lastReference: string
}

export type ReviewDetailApi = {
  id: string
  taskId: string
  taskName: string
  module: string
  moduleName: string
  cycle: string
  status: string
  submitTime: string
  reviewer: string
  commentSummary: string
  nextStep: string
  rectifyDeadline?: string
  correctionDeadline?: string
}

export type ReviewTimelineApi = {
  id: number | string
  reviewId: string
  action: string
  operatorId?: number
  operatorName: string
  operatedAt: string
}

export type ReviewRequirementApi = {
  id: number | string
  reviewId: string
  requirementText: string
  deadline?: string
  status?: string
}

export type ReviewActionResponse = {
  ok: boolean
  reviewId: string
  taskId: string
  status: string
  taskStatus?: string
  message: string
  requirements?: string[]
}

export type TaskDetailApi = {
  task: UploadTask
  tabs: string[]
  documents: TaskDocumentApi[]
  linkedDocuments: LinkedDocumentApi[]
  validation: {
    completed: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
  validationIssues: ValidationIssueApi[]
  candidateDocuments: CandidateDocumentApi[]
  aiRecommendation?: {
    fileName: string
    matchRate: number
    text: string
  }
  aiTip?: string
  reviewTimeline: { time: string; action: string }[]
  reviewRecords: TaskReviewRecordApi[]
}

export type TaskDocumentApi = {
  id: string
  name: string
  required: boolean
  format: string
  status: string
  templateAvailable: boolean
}

export type LinkedDocumentApi = {
  relationId: number | string
  documentId: string
  documentName: string
  documentType: string
  period: string
  version: string
  validityStatus: string
  source: string
  relationType: string
  relationStatus: string
  matchScore: number
  linkedAt: string
  uploadedAt: string
}

export type ValidationIssueApi = {
  id: string
  documentRequirementId: string
  documentName: string
  issueType: string
  severity: string
  message: string
  canSubmit: boolean
}

export type CandidateDocumentApi = {
  id: string
  documentId?: string | null
  requirementId?: string | null
  name: string
  cycle: string
  unit: string
  linkCount: number
  matchRate: number
}

export type TaskReviewRecordApi = {
  id: number | string
  taskId: string
  taskName: string
  submitTime: string
  status: string
  reviewer: string
  commentSummary: string
  nextStep: string
}

export type TaskActionResponse = {
  ok: boolean
  taskId?: string
  status?: string
  message?: string
  reviewId?: string
  documentId?: string
  requirementId?: string | null
  requirementName?: string | null
  progress?: {
    completed: number
    total: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
  validation?: {
    completed: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
}
