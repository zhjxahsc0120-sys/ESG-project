export type EsgModule = 'E' | 'S' | 'G'
export type TaskStatus = '待上传' | '待补正' | '待提交' | '审核中' | '审核退回' | '已完成' | '已归档'
export type ReviewStatus = '待审核' | '已通过' | '已退回' | '补正逾期'

export interface StatusCard {
  label: string
  value: number
  unit?: string
  subText?: string
  color: string
}

export interface UploadTask {
  id: string
  name: string
  module: EsgModule
  moduleName: string
  deadline: string
  deadlineDisplay: string
  progressCurrent: number
  progressTotal: number
  status: TaskStatus
  nextStep: string
  daysOverdue?: number
  daysRemaining?: number
  hoursRemaining?: number
  cycle?: string
  cycleType?: '月度' | '季度' | '年度' | '一次性'
  assignee?: string
  assigneeDept?: string
}

export interface DocumentRelatedTask {
  module: EsgModule
  name: string
  cycle: string
  status: string
  referenceCount: number
  lastReference: string
}

export interface Document {
  id: string
  name: string
  type: string
  module?: string
  cycle: string
  version: string
  source: string
  relatedTaskCount: number
  status: '有效' | '即将失效' | '已失效'
  size?: string
  uploadTime?: string
  creator?: string
  format?: string
  pages?: number
  tags?: string[]
  isUnique?: boolean
  relatedTasks?: DocumentRelatedTask[]
}

export interface ParseQueueItem {
  id: string
  jobId?: number
  fileId?: number
  fileName: string
  size: string
  progress: number
  status: string
}

export interface AiParseResult {
  documentType: string
  cycle: string
  module: EsgModule
  moduleName: string
  responsibilityUnit: string
  validPeriod: string
  duplicateCount: number
  duplicateTip: string
}

export interface SuggestedTask {
  id: string
  documentName: string
  taskName: string
  module: EsgModule
  moduleName: string
  matchRate: number
  reuseCount: number
  confirmStatus: string
}

export interface ReviewRecord {
  id: string
  taskId?: string
  taskName: string
  module: EsgModule
  moduleName: string
  submitTime: string
  status: ReviewStatus
  reviewer: string
  commentSummary: string
  nextStep: string
}

export interface ReviewTimeline {
  time: string
  action: string
}

export interface ReviewRequirement {
  id: string
  requirement: string
}

export interface TaskDocument {
  id: string
  name: string
  required: boolean
  format: string
  status: '已关联' | '缺失' | '格式异常' | '待上传' | '审核通过'
  templateAvailable: boolean
}

export interface TodayFocus {
  id: string
  name: string
  type: 'remaining' | 'overdue' | 'urgent' | 'today'
  value: string
}

export interface QuickQuestion {
  id: string
  question: string
}
