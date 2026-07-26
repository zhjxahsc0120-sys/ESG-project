<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Upload,
  FolderOpen,
  Link2,
  FileText,
  FileImage,
  FileSpreadsheet,
  AlertTriangle,
  Search,
  RefreshCw,
  Trash2,
  XCircle,
  Copy,
  Eye,
  Sparkles,
  Layers,
  ChevronLeft,
  ChevronRight,
} from 'lucide-vue-next'
import {
  parseQueue as mockParseQueue,
  documents as mockDocuments,
} from '@/data/workspace.mock'
import {
  getParseQueue,
  uploadWorkspaceBinaryFile,
  startParseFile,
  getParseJob,
  getParseFields,
  getMatchCandidates,
  confirmParseJob,
} from '@/services/api'
import type { ParseQueueItem, AiParseResult, SuggestedTask, Document, DuplicateFileInfo } from '@/types/workspace'
import type { ParseFieldItem, MatchCandidateItem, ParseJobDetail } from '@/services/api'
import { emitWorkspaceRefresh, onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const EMPTY_PARSE_RESULT: AiParseResult = {
  documentType: '—',
  cycle: '—',
  module: 'E',
  moduleName: '环境环保',
  responsibilityUnit: '—',
  projectSection: '—',
  engineeringObject: '—',
  validPeriod: '—',
  suggestedTask: '—',
  suggestedKpiCode: '',
  suggestedKpiName: '上传文件后自动识别',
  suggestedReport: '',
  confidence: 0,
  duplicateCount: 0,
  duplicateTip: '',
}

const SAMPLE_FILE_URL = '/samples/%E7%BD%97%E5%AE%9C%E9%AB%98%E9%80%9F_2026%E5%B9%B47%E6%9C%88%E6%B0%B4%E4%BF%9D%E7%9B%91%E6%B5%8B%E6%9C%88%E6%8A%A5%E6%91%98%E8%A6%81.csv'
const SAMPLE_FILE_NAME = '罗宜高速_2026年7月水保监测月报摘要.csv'

const showUploadArea = ref(true)
const selectedTasks = ref<string[]>([])
const parseQueueList = ref<ParseQueueItem[]>([...mockParseQueue])
const aiParseResult = ref<AiParseResult>({ ...EMPTY_PARSE_RESULT })
const suggestedTasks = ref<SuggestedTask[]>([])
const extractedFields = ref<ParseFieldItem[]>([])
const hasRealParse = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)

const currentFileId = ref<number | null>(null)
const currentJobId = ref<number | null>(null)
const currentJob = ref<ParseJobDetail | null>(null)
const pageMessage = ref('')
const pageMessageType = ref<'success' | 'error' | 'info'>('info')

const statusFilter = ref<string>('全部')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = 10
const selectedQueueItems = ref<string[]>([])
const showDuplicateModal = ref(false)
const currentDuplicateFile = ref<DuplicateFileInfo | null>(null)
const editingField = ref<string | null>(null)
const editFieldValue = ref('')

const statusOptions = ['全部', '解析中', '待确认', '疑似重复', '解析失败', '已入库']

function showMessage(message: string, type: 'success' | 'error' | 'info' = 'info') {
  pageMessage.value = message
  pageMessageType.value = type
}

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.scopes.includes('parse-queue')) {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const data = await getParseQueue()
  if (data && data.items && data.items.length > 0) {
    parseQueueList.value = data.items as ParseQueueItem[]
  }
}

async function loadJobDetails(jobId: number) {
  const [jobRes, fieldsRes, candidatesRes] = await Promise.all([
    getParseJob(jobId),
    getParseFields(jobId),
    getMatchCandidates(jobId),
  ])
  if (jobRes) currentJob.value = jobRes
  if (fieldsRes && fieldsRes.items.length > 0) {
    extractedFields.value = fieldsRes.items
    updateAiResultFromFields(fieldsRes.items, jobRes)
    hasRealParse.value = true
  }
  if (candidatesRes && candidatesRes.items.length > 0) {
    updateCandidatesFromApi(candidatesRes.items, currentJob.value?.fileName || '')
    if (!aiParseResult.value.suggestedTask || aiParseResult.value.suggestedTask === '—') {
      aiParseResult.value.suggestedTask = suggestedTasks.value[0]?.taskName || '—'
    }
  } else {
    suggestedTasks.value = []
    selectedTasks.value = []
  }
}

function avgConfidence(fields: ParseFieldItem[]): number {
  if (!fields.length) return 0
  const sum = fields.reduce((acc, f) => acc + (Number(f.confidence) || 0), 0)
  return Math.round(sum / fields.length)
}

function updateAiResultFromFields(fields: ParseFieldItem[], job?: ParseJobDetail | null) {
  const map: Record<string, string> = {}
  for (const f of fields) {
    map[f.fieldKey] = f.fieldValue
  }
  const module = (map['esg_module'] || map['module'] || 'E') as 'E' | 'S' | 'G'
  const validStart = map['valid_start_date'] || ''
  const validEnd = map['valid_end_date'] || ''
  const validPeriod = validStart && validEnd ? `${validStart} ~ ${validEnd}` : (validStart || validEnd || '—')
  const conf = job?.confidence != null ? Math.round(Number(job.confidence)) : avgConfidence(fields)
  aiParseResult.value = {
    documentType: map['document_type'] || '—',
    cycle: map['period'] || '—',
    module,
    moduleName: module === 'E' ? '环境环保' : module === 'S' ? '社会责任' : module === 'G' ? '治理合规' : '环境环保',
    responsibilityUnit: map['responsible_unit'] || map['responsibility_unit'] || '—',
    projectSection: map['project_section'] || '—',
    engineeringObject: map['engineering_object'] || '—',
    validPeriod,
    suggestedTask: map['suggested_task'] || suggestedTasks.value[0]?.taskName || '—',
    suggestedKpiCode: map['suggested_kpi_code'] || '',
    suggestedKpiName: map['suggested_kpi_name'] || '',
    suggestedReport: map['period'] ? `${map['period']} ESG月报` : '',
    confidence: conf,
    duplicateCount: 0,
    duplicateTip: '',
  }
}

function updateCandidatesFromApi(candidates: MatchCandidateItem[], fileName: string) {
  suggestedTasks.value = candidates.map(c => ({
    id: String(c.candidateId),
    documentName: fileName,
    taskName: c.taskName,
    module: c.module as 'E' | 'S' | 'G',
    moduleName: c.module === 'E' ? '环境环保' : c.module === 'S' ? '社会责任' : '治理合规',
    matchRate: c.matchScore,
    reuseCount: c.reuseCount,
    confirmStatus: c.candidateStatus === 'PENDING' ? '待确认' : c.candidateStatus === 'ACCEPTED' ? '已关联' : c.candidateStatus,
    matchBasis: c.matchReason,
  }))
  if (candidates.length > 0) {
    const best = candidates.reduce((a, b) => (a.matchScore > b.matchScore ? a : b))
    selectedTasks.value = [String(best.candidateId)]
  }
}

function handleSelectFile() {
  fileInputRef.value?.click()
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  hasRealParse.value = false
  extractedFields.value = []
  aiParseResult.value = { ...EMPTY_PARSE_RESULT }
  suggestedTasks.value = []
  selectedTasks.value = []

  const uploadRes = await uploadWorkspaceBinaryFile(file, {
    uploaderId: 10001,
    uploaderName: '项目管理员',
  })
  if (uploadRes) {
    currentFileId.value = uploadRes.fileId
    if (uploadRes.duplicateStatus === 'DUPLICATE') {
      showMessage(`文件已接收，但检测到相同哈希文件。当前文件ID：${uploadRes.fileId}，匹配文件ID：${uploadRes.matchedFileId || '-'}`, 'info')
    } else {
      showMessage(`文件已接收并写入存储区。文件ID：${uploadRes.fileId}`, 'success')
    }
    const parseRes = await startParseFile(uploadRes.fileId)
    if (parseRes) {
      currentJobId.value = parseRes.jobId
      await loadData()
      await loadJobDetails(parseRes.jobId)
      const sourceHint = currentJob.value?.parseSource === 'content'
        ? '已从文件内容识别字段'
        : '已按文件名规则识别'
      const summaryHint = currentJob.value?.summary ? `：${currentJob.value.summary}` : ''
      showMessage(`${sourceHint}${summaryHint}。JobID：${parseRes.jobId}`, 'success')
    }
  } else {
    showMessage('上传接口未响应，请确认后端已启动。', 'error')
  }
  input.value = ''
}

function handleDownloadSample() {
  const link = document.createElement('a')
  link.href = SAMPLE_FILE_URL
  link.download = SAMPLE_FILE_NAME
  link.click()
}

function handleBatchImport() {
  showMessage('批量导入功能为原型预留，暂未接入批量导入流程。', 'info')
}

function handleSelectFromCenter() {
  showMessage('从资料中心选择功能为原型预留，暂未接入选择器。', 'info')
}

function toggleTaskSelect(taskId: string) {
  const index = selectedTasks.value.indexOf(taskId)
  if (index > -1) {
    selectedTasks.value.splice(index, 1)
  } else {
    selectedTasks.value.push(taskId)
  }
}

function handleCancel() {
  showMessage('已取消当前操作。', 'info')
}

function handleSaveToCenter() {
  showMessage('保存到资料中心为原型预留操作；如需真实入库，请使用"确认入库并关联"。', 'info')
}

async function handleConfirmAndLink() {
  if (!currentJobId.value) {
    showMessage('请先上传并解析文件。', 'error')
    return
  }
  const confirmedFields = suggestedTasks.value.length > 0
    ? [{ fieldKey: 'document_type', confirmedValue: aiParseResult.value.documentType }]
    : []
  const acceptedCandidateIds = selectedTasks.value
    .map(id => Number(id))
    .filter(id => !isNaN(id))
  const res = await confirmParseJob(currentJobId.value, {
    confirmedFields,
    acceptedCandidateIds,
    operatorId: 10001,
    operatorName: '项目管理员',
    comment: '前端确认入库',
  })
  if (res) {
    const linkedSummary = res.linkedTasks && res.linkedTasks.length > 0
      ? res.linkedTasks.map(task => {
        const progress = task.progress ? `${task.progress.completed}/${task.progress.total}` : '-'
        return `${task.taskName}${task.requirementName ? `：${task.requirementName}` : ''}（完整度 ${progress}）`
      }).join('；')
      : '未关联任务'
    showMessage(`资料已入库并关联 ${res.linkedTaskCount} 个任务。DocumentID：${res.documentId}。${linkedSummary}`, 'success')
    await loadData()
    emitWorkspaceRefresh({
      source: 'smart-upload',
      scopes: ['summary', 'tasks', 'documents', 'parse-queue'],
    })
    currentJobId.value = null
    currentJob.value = null
  } else {
    showMessage('确认入库接口未响应。', 'error')
  }
}

function handleViewParseDetail() {
  if (!currentJobId.value) {
    showMessage('请先上传样例文件完成解析。', 'info')
    return
  }
  loadJobDetails(currentJobId.value)
  const engine = currentJob.value?.parseEngine || '解析引擎'
  const count = extractedFields.value.length
  showMessage(`${engine}：已识别 ${count} 个字段${currentJob.value?.summary ? `；${currentJob.value.summary}` : ''}`, 'info')
}

const highlightFieldKeys = [
  'dust_exceed_count',
  'noise_exceed_count',
  'water_protection_issue_count',
  'monitor_date',
  'summary_note',
]

const highlightFields = computed(() =>
  extractedFields.value.filter(f => highlightFieldKeys.includes(f.fieldKey)),
)

function handleViewDuplicateDetail(item: ParseQueueItem) {
  currentDuplicateFile.value = {
    id: item.id,
    fileName: item.fileName,
    fileHash: item.fileHash || 'SHA256: a1b2c3d4e5f6...',
    fileSize: item.size,
    cycle: aiParseResult.value.cycle,
    uploadTime: item.uploadTime || '2026-08-10 16:20',
    relatedTasks: ['2026年7月水保监测月报', '临时用地合规资料'],
    similarity: 95,
  }
  showDuplicateModal.value = true
}

function handleViewFile(fileName: string) {
  showMessage(`文件预览为原型展示，未接入真实文件存储服务。文件：${fileName}`, 'info')
}

function handleViewLink(taskName: string) {
  showMessage(`查看关联详情为原型展示。任务：${taskName}`, 'info')
}

async function handleViewResult(item: ParseQueueItem) {
  if (item.status === '疑似重复') {
    handleViewDuplicateDetail(item)
    return
  }
  if (item.jobId) {
    currentJobId.value = item.jobId
    await loadJobDetails(item.jobId)
  } else if (currentJobId.value) {
    await loadJobDetails(currentJobId.value)
  } else {
    showMessage(`当前队列项：${item.fileName}`, 'info')
  }
}

function getModuleColor(module: string) {
  switch (module) {
    case 'E': return '#69e36f'
    case 'S': return '#2f9cff'
    case 'G': return '#a66cff'
    default: return '#8fa9c8'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case '已关联': return '#69e36f'
    case '匹配中': return '#2f9cff'
    case '待确认': return '#ffb347'
    case '解析中': return '#2f9cff'
    case '已入库': return '#69e36f'
    case '疑似重复': return '#ffb347'
    case '解析失败': return '#ff4f5e'
    default: return '#8fa9c8'
  }
}

function isSelected(taskId: string) {
  return selectedTasks.value.includes(taskId)
}

function getFileIcon(fileName: string) {
  if (fileName.endsWith('.pdf')) return FileText
  if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileName.endsWith('.csv')) return FileSpreadsheet
  if (fileName.endsWith('.jpg') || fileName.endsWith('.png') || fileName.endsWith('.jpeg')) return FileImage
  return FileText
}

function getQueueButtonAction(status: string): string {
  if (status === '解析完成' || status === '已入库' || status === '待确认') return '查看结果'
  if (status.includes('匹配中') || status.includes('解析中')) return '查看进度'
  if (status === '疑似重复') return '处理重复'
  if (status.includes('失败')) return '重新解析'
  return '查看'
}

const filteredQueue = computed(() => {
  let list = parseQueueList.value
  if (statusFilter.value !== '全部') {
    list = list.filter(item => item.status === statusFilter.value)
  }
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    list = list.filter(item => item.fileName.toLowerCase().includes(keyword))
  }
  return list
})

const paginatedQueue = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredQueue.value.slice(start, start + pageSize)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredQueue.value.length / pageSize)))

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function getPageNumbers(): number[] {
  const pages: number[] = []
  const maxPages = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2))
  let end = Math.min(totalPages.value, start + maxPages - 1)
  if (end - start + 1 < maxPages) {
    start = Math.max(1, end - maxPages + 1)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
}

watch(filteredQueue, () => {
  currentPage.value = 1
})

function toggleQueueItemSelect(id: string) {
  const idx = selectedQueueItems.value.indexOf(id)
  if (idx > -1) {
    selectedQueueItems.value.splice(idx, 1)
  } else {
    selectedQueueItems.value.push(id)
  }
}

const isAllSelected = computed(() => {
  return paginatedQueue.value.length > 0 && paginatedQueue.value.every(item => selectedQueueItems.value.includes(item.id))
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedQueueItems.value = selectedQueueItems.value.filter(id => !paginatedQueue.value.some(item => item.id === id))
  } else {
    for (const item of paginatedQueue.value) {
      if (!selectedQueueItems.value.includes(item.id)) {
        selectedQueueItems.value.push(item.id)
      }
    }
  }
}

function handleRetryParse(item: ParseQueueItem) {
  showMessage(`正在重新解析文件：${item.fileName}`, 'info')
  const idx = parseQueueList.value.findIndex(i => i.id === item.id)
  if (idx > -1) {
    parseQueueList.value[idx].status = '解析中'
    parseQueueList.value[idx].progress = 0
  }
}

function handleClearFailed(item: ParseQueueItem) {
  const idx = parseQueueList.value.findIndex(i => i.id === item.id)
  if (idx > -1) {
    parseQueueList.value.splice(idx, 1)
    showMessage(`已清除失败记录：${item.fileName}`, 'success')
  }
}

function handleBatchRetry() {
  const failedItems = selectedQueueItems.value
    .map(id => parseQueueList.value.find(i => i.id === id))
    .filter(i => i && i.status === '解析失败') as ParseQueueItem[]
  if (failedItems.length === 0) {
    showMessage('请先选择解析失败的文件', 'info')
    return
  }
  for (const item of failedItems) {
    handleRetryParse(item)
  }
  showMessage(`已批量重新解析 ${failedItems.length} 个文件`, 'success')
}

function handleBatchClearFailed() {
  const failedItems = selectedQueueItems.value
    .map(id => parseQueueList.value.find(i => i.id === id))
    .filter(i => i && i.status === '解析失败') as ParseQueueItem[]
  if (failedItems.length === 0) {
    showMessage('请先选择解析失败的文件', 'info')
    return
  }
  for (const item of failedItems) {
    const idx = parseQueueList.value.findIndex(i => i.id === item.id)
    if (idx > -1) {
      parseQueueList.value.splice(idx, 1)
    }
  }
  selectedQueueItems.value = []
  showMessage(`已批量清除 ${failedItems.length} 条失败记录`, 'success')
}

function startEditField(field: string, value: string) {
  editingField.value = field
  editFieldValue.value = value
}

function saveEditField(field: string) {
  if (field === 'documentType') aiParseResult.value.documentType = editFieldValue.value
  if (field === 'cycle') aiParseResult.value.cycle = editFieldValue.value
  if (field === 'responsibilityUnit') aiParseResult.value.responsibilityUnit = editFieldValue.value
  if (field === 'projectSection') aiParseResult.value.projectSection = editFieldValue.value
  if (field === 'engineeringObject') aiParseResult.value.engineeringObject = editFieldValue.value
  if (field === 'validPeriod') aiParseResult.value.validPeriod = editFieldValue.value
  if (field === 'suggestedTask') aiParseResult.value.suggestedTask = editFieldValue.value
  if (field === 'suggestedKpiName') aiParseResult.value.suggestedKpiName = editFieldValue.value
  editingField.value = null
  showMessage('已保存修改', 'success')
}

function cancelEditField() {
  editingField.value = null
}

function handleReuseExisting() {
  showMessage('已复用已有资料，取消当前上传', 'success')
  showDuplicateModal.value = false
}

function handleUploadAsNewVersion() {
  showMessage('已作为新版本上传', 'success')
  showDuplicateModal.value = false
}

function handleConfirmDifferent() {
  showMessage('已确认为不同资料，继续处理', 'success')
  showDuplicateModal.value = false
  const idx = parseQueueList.value.findIndex(i => i.id === currentDuplicateFile.value?.id)
  if (idx > -1) {
    parseQueueList.value[idx].status = '待确认'
  }
}

function handleCancelUpload() {
  showDuplicateModal.value = false
}

function handleReuseAndRecommend(task: SuggestedTask) {
  showMessage(`已复用并关联：${task.taskName}`, 'success')
}

function handleIgnoreRecommend(task: SuggestedTask) {
  const idx = suggestedTasks.value.findIndex(t => t.id === task.id)
  if (idx > -1) {
    suggestedTasks.value.splice(idx, 1)
  }
  showMessage('已忽略该推荐', 'info')
}

const existingDocForRecommend = computed<Document | null>(() => {
  return mockDocuments.find(d => d.id === 'd1') || null
})

const hasUnprocessedDuplicate = computed(() => {
  return parseQueueList.value.some(item => item.status === '疑似重复')
})

const recPageSize = 3
const recCurrentPage = ref(1)

const allRecommendedTasks = computed<SuggestedTask[]>(() => {
  const seen = new Set<string>()
  const unique: SuggestedTask[] = []
  for (const task of suggestedTasks.value) {
    if (seen.has(task.id)) continue
    seen.add(task.id)
    unique.push(task)
  }
  return unique
})

const recTotalPages = computed(() => Math.max(1, Math.ceil(allRecommendedTasks.value.length / recPageSize)))

const recommendedTasks = computed<SuggestedTask[]>(() => {
  const start = (recCurrentPage.value - 1) * recPageSize
  return allRecommendedTasks.value.slice(start, start + recPageSize)
})

function goToRecPage(page: number) {
  if (page < 1 || page > recTotalPages.value) return
  recCurrentPage.value = page
}
</script>

<template>
  <div class="workspace-smart-upload ws-page">
    <div v-if="pageMessage" class="ws-page-message" :class="pageMessageType">{{ pageMessage }}</div>

    <div class="main-content">
      <div class="left-section">
        <div class="upload-section ws-panel">
          <input
            ref="fileInputRef"
            class="hidden-file-input"
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.jpg,.jpeg,.png,.zip,.rar"
            @change="handleFileChange"
          />
          <div class="ws-panel-header">
            <div class="ws-panel-title">上传资料</div>
          </div>

          <div class="upload-area" @click="handleSelectFile">
            <div class="upload-icon">
              <Upload :size="20" />
            </div>
            <div class="upload-text">将文件拖拽到此处，或选择文件上传</div>
          </div>

          <div class="upload-desc">
            支持 PDF、Word、Excel、CSV、TXT、图片及压缩包。演示建议：{{ SAMPLE_FILE_NAME }}
          </div>

          <div class="upload-buttons">
            <button class="ws-btn ws-btn-primary" @click="handleSelectFile">
              <Upload :size="14" />
              <span>选择本地文件</span>
            </button>
            <button class="ws-btn ws-btn-secondary" @click="handleDownloadSample">
              <FileSpreadsheet :size="14" />
              <span>下载样例文件</span>
            </button>
            <button class="ws-btn ws-btn-secondary" @click="handleBatchImport">
              <FolderOpen :size="14" />
              <span>批量导入</span>
            </button>
            <button class="ws-btn ws-btn-secondary" @click="handleSelectFromCenter">
              <Link2 :size="14" />
              <span>从资料中心选择</span>
            </button>
          </div>
        </div>

        <div class="parse-queue-section ws-panel">
          <div class="ws-panel-header">
            <div class="ws-panel-title">解析队列</div>
            <div class="queue-actions">
              <button class="ws-btn ws-btn-secondary ws-btn-sm" @click="handleBatchRetry" :disabled="selectedQueueItems.length === 0">
                <RefreshCw :size="14" />
                <span>批量重解析</span>
              </button>
              <button class="ws-btn ws-btn-danger ws-btn-sm" @click="handleBatchClearFailed" :disabled="selectedQueueItems.length === 0">
                <Trash2 :size="14" />
                <span>清除失败</span>
              </button>
            </div>
          </div>

          <div class="queue-filters">
            <div class="status-tabs">
              <span
                v-for="status in statusOptions"
                :key="status"
                class="status-tab"
                :class="{ active: statusFilter === status }"
                @click="statusFilter = status; currentPage = 1"
              >{{ status }}</span>
            </div>
            <div class="ws-search-box queue-search">
              <Search :size="14" />
              <input v-model="searchKeyword" type="text" placeholder="搜索文件名..." @input="currentPage = 1" />
            </div>
          </div>

          <div class="ws-table-container queue-table">
            <div class="ws-table-scroll no-scroll">
              <table class="ws-table">
                <colgroup>
                  <col class="col-checkbox" />
                  <col class="col-file" />
                  <col class="col-size" />
                  <col class="col-progress" />
                  <col class="col-status" />
                  <col class="col-time" />
                  <col class="col-action" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-checkbox">
                      <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll" />
                    </th>
                    <th class="col-file">文件名</th>
                    <th class="col-size">大小</th>
                    <th class="col-progress">进度</th>
                    <th class="col-status">状态</th>
                    <th class="col-time">上传时间</th>
                    <th class="col-action">下一步</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedQueue" :key="item.id" :class="{ selected: selectedQueueItems.includes(item.id) }">
                    <td class="col-checkbox">
                      <input type="checkbox" :checked="selectedQueueItems.includes(item.id)" @change="toggleQueueItemSelect(item.id)" />
                    </td>
                    <td class="col-file">
                      <component :is="getFileIcon(item.fileName)" :size="14" class="file-icon" />
                      <span class="file-name-text">{{ item.fileName }}</span>
                    </td>
                    <td class="col-size">{{ item.size }}</td>
                    <td class="col-progress">
                      <div class="ws-progress">
                        <div class="ws-progress-bar">
                          <div class="ws-progress-fill" :style="{ width: `${item.progress}%` }"></div>
                        </div>
                        <span class="ws-progress-text">{{ item.progress }}%</span>
                      </div>
                    </td>
                    <td class="col-status">
                      <span class="status-tag" :style="{ background: `${getStatusColor(item.status)}20`, color: getStatusColor(item.status) }">
                        {{ item.status }}
                      </span>
                    </td>
                    <td class="col-time">{{ item.uploadTime || '-' }}</td>
                    <td class="col-action">
                      <button class="ws-btn ws-btn-action ws-btn-sm" @click.stop="handleViewResult(item)">
                        {{ getQueueButtonAction(item.status) }}
                      </button>
                      <button v-if="item.status === '解析失败'" class="ws-btn ws-btn-secondary ws-btn-sm" @click.stop="handleRetryParse(item)">
                        <RefreshCw :size="12" />
                      </button>
                      <button v-if="item.status === '解析失败'" class="ws-btn ws-btn-danger ws-btn-sm" @click.stop="handleClearFailed(item)">
                        <Trash2 :size="12" />
                      </button>
                    </td>
                  </tr>
                  <tr v-if="paginatedQueue.length === 0">
                    <td colspan="7" class="empty-row">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="ws-pagination-bar">
            <div class="ws-pagination-info">共 <span class="highlight">{{ filteredQueue.length }}</span> 项，每页 {{ pageSize }} 项</div>
            <div class="ws-pagination-controls">
              <button class="ws-page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
                <ChevronLeft :size="14" />
              </button>
              <button
                v-for="p in getPageNumbers()"
                :key="p"
                class="ws-page-btn"
                :class="{ active: currentPage === p }"
                @click="goToPage(p)"
              >
                {{ p }}
              </button>
              <button class="ws-page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
                <ChevronRight :size="14" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="right-section">
        <div class="ai-summary-card ws-panel">
          <div class="ws-panel-header">
            <div class="ws-panel-title">
              <Sparkles :size="16" class="ws-panel-title-icon" />
              <span>AI解析摘要</span>
            </div>
            <div class="summary-header-actions">
              <span
                v-if="hasRealParse"
                class="parse-source-badge"
                :title="currentJob?.summary || ''"
              >
                {{ currentJob?.parseSource === 'content' ? '已识别' : '规则识别' }}
              </span>
              <button class="detail-btn" @click="handleViewParseDetail">查看详情</button>
            </div>
          </div>
          <div v-if="!hasRealParse" class="parse-empty-hint">
            上传样例 CSV 后，此处展示从文件内容识别的字段与置信度。
          </div>
          <div class="ai-fields">
            <div class="ai-field">
              <span class="field-label">资料类型</span>
              <div v-if="editingField === 'documentType'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('documentType')" @blur="saveEditField('documentType')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('documentType', aiParseResult.documentType)">
                <span class="field-value">{{ aiParseResult.documentType }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">资料周期</span>
              <div v-if="editingField === 'cycle'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('cycle')" @blur="saveEditField('cycle')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('cycle', aiParseResult.cycle)">
                <span class="field-value">{{ aiParseResult.cycle }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">ESG模块</span>
              <span class="field-value" :style="{ color: getModuleColor(aiParseResult.module) }">
                {{ aiParseResult.module }} · {{ aiParseResult.moduleName }}
              </span>
            </div>
            <div class="ai-field">
              <span class="field-label">责任单位</span>
              <div v-if="editingField === 'responsibilityUnit'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('responsibilityUnit')" @blur="saveEditField('responsibilityUnit')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('responsibilityUnit', aiParseResult.responsibilityUnit)">
                <span class="field-value">{{ aiParseResult.responsibilityUnit }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">项目/标段</span>
              <div v-if="editingField === 'projectSection'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('projectSection')" @blur="saveEditField('projectSection')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('projectSection', aiParseResult.projectSection || '-')">
                <span class="field-value">{{ aiParseResult.projectSection || '-' }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">工程对象/事项</span>
              <div v-if="editingField === 'engineeringObject'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('engineeringObject')" @blur="saveEditField('engineeringObject')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('engineeringObject', aiParseResult.engineeringObject || '-')">
                <span class="field-value">{{ aiParseResult.engineeringObject || '-' }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">有效期</span>
              <div v-if="editingField === 'validPeriod'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('validPeriod')" @blur="saveEditField('validPeriod')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('validPeriod', aiParseResult.validPeriod)">
                <span class="field-value">{{ aiParseResult.validPeriod }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">建议关联任务</span>
              <div v-if="editingField === 'suggestedTask'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('suggestedTask')" @blur="saveEditField('suggestedTask')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('suggestedTask', aiParseResult.suggestedTask)">
                <span class="field-value link-like">{{ aiParseResult.suggestedTask }}</span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field">
              <span class="field-label">建议关联指标</span>
              <div v-if="editingField === 'suggestedKpiName'" class="field-edit">
                <input v-model="editFieldValue" class="edit-input" @keyup.enter="saveEditField('suggestedKpiName')" @blur="saveEditField('suggestedKpiName')" />
              </div>
              <div v-else class="field-value-wrap" @dblclick="startEditField('suggestedKpiName', aiParseResult.suggestedKpiCode + ' ' + aiParseResult.suggestedKpiName)">
                <span class="field-value kpi-value">
                  <span class="kpi-code">{{ aiParseResult.suggestedKpiCode }}</span>
                  {{ aiParseResult.suggestedKpiName }}
                </span>
                <span class="edit-hint">双击编辑</span>
              </div>
            </div>
            <div class="ai-field confidence-field">
              <span class="field-label">解析置信度</span>
              <div class="confidence-wrap">
                <div class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: `${aiParseResult.confidence}%` }"></div>
                </div>
                <span class="confidence-text">{{ aiParseResult.confidence }}%</span>
              </div>
            </div>
          </div>

          <div v-if="highlightFields.length" class="extracted-metrics">
            <div class="extracted-metrics-title">自文件识别的业务字段</div>
            <div
              v-for="field in highlightFields"
              :key="field.id"
              class="extracted-metric-row"
            >
              <span class="metric-name">{{ field.fieldName }}</span>
              <span class="metric-value">{{ field.fieldValue }}</span>
              <span class="metric-conf">{{ Math.round(Number(field.confidence) || 0) }}%</span>
            </div>
          </div>

          <div v-if="aiParseResult.duplicateCount > 0" class="duplicate-warning" @click="showDuplicateModal = true">
            <AlertTriangle :size="16" class="warning-icon" />
            <span class="warning-text">疑似重复</span>
            <span class="warning-count">{{ aiParseResult.duplicateCount }}份</span>
            <span class="warning-btn-text">点击处理 →</span>
          </div>
        </div>

        <div class="ai-recommend-card ws-panel">
          <div class="ws-panel-header">
            <div class="ws-panel-title">
              <Layers :size="16" class="ws-panel-title-icon" />
              <span>AI智能推荐</span>
            </div>
            <span class="rec-count">共 {{ allRecommendedTasks.length }} 条</span>
          </div>
          <div class="recommend-list">
            <div v-if="recommendedTasks.length === 0" class="parse-empty-hint">
              上传并解析后，此处显示匹配到的上传任务候选。
            </div>
            <div v-for="task in recommendedTasks" :key="task.id" class="recommend-item">
              <div class="recommend-file-info">
                <div class="recommend-file-name">
                  <FileText :size="16" class="recommend-file-icon" />
                  <span :title="task.documentName">{{ task.documentName }}</span>
                </div>
                <div class="recommend-meta">
                  <span class="match-badge" :style="{ color: getModuleColor(task.module), borderColor: getModuleColor(task.module) + '50' }">
                    匹配度 {{ task.matchRate }}%
                  </span>
                  <span class="reuse-count">已关联 {{ task.reuseCount }} 个任务</span>
                </div>
                <div class="recommend-basis">
                  <span class="basis-label">推荐依据：</span>
                  <span class="basis-text" :title="task.matchBasis">{{ task.matchBasis || '内容关键词匹配' }}</span>
                </div>
              </div>
              <div class="recommend-actions">
                <button class="ws-btn ws-btn-primary ws-btn-sm" @click="handleReuseAndRecommend(task)">复用并关联</button>
                <button class="ws-btn ws-btn-secondary ws-btn-sm" @click="handleViewFile(task.documentName)">
                  <Eye :size="12" />
                  <span>查看</span>
                </button>
                <button class="ws-btn ws-btn-secondary ws-btn-sm" @click="handleIgnoreRecommend(task)">
                  <XCircle :size="12" />
                  <span>忽略</span>
                </button>
              </div>
            </div>
          </div>
          <div v-if="allRecommendedTasks.length > recPageSize" class="rec-pagination">
            <span class="rec-pagination-info">共 {{ allRecommendedTasks.length }} 条</span>
            <div class="rec-pagination-controls">
              <button class="rec-page-btn" :disabled="recCurrentPage === 1" @click="goToRecPage(recCurrentPage - 1)">上一页</button>
              <button
                v-for="p in recTotalPages"
                :key="p"
                class="rec-page-btn"
                :class="{ active: recCurrentPage === p }"
                @click="goToRecPage(p)"
              >{{ p }}</button>
              <button class="rec-page-btn" :disabled="recCurrentPage === recTotalPages" @click="goToRecPage(recCurrentPage + 1)">下一页</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="ws-bottom-actions">
      <button class="ws-btn ws-btn-secondary" @click="handleCancel">取消</button>
      <button class="ws-btn ws-btn-view" @click="handleSaveToCenter">仅保存到资料中心</button>
      <button class="ws-btn ws-btn-primary" :disabled="hasUnprocessedDuplicate" @click="handleConfirmAndLink">
        确认入库并关联
      </button>
    </div>

    <div v-if="showDuplicateModal" class="modal-overlay" @click.self="showDuplicateModal = false">
      <div class="modal duplicate-modal">
        <div class="modal-header">
          <span class="modal-title">
            <AlertTriangle :size="18" class="modal-title-icon" />
            疑似重复资料
          </span>
          <button class="modal-close" @click="showDuplicateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="duplicate-compare">
            <div class="compare-col">
              <div class="compare-label new-label">
                <Upload :size="14" />
                <span>新上传文件</span>
              </div>
              <div class="compare-content">
                <div class="compare-item">
                  <span class="compare-key">文件名</span>
                  <span class="compare-val">{{ currentDuplicateFile?.fileName }}</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">文件哈希</span>
                  <span class="compare-val hash">{{ currentDuplicateFile?.fileHash }}</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">文件大小</span>
                  <span class="compare-val">{{ currentDuplicateFile?.fileSize }}</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">资料周期</span>
                  <span class="compare-val">{{ currentDuplicateFile?.cycle }}</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">上传时间</span>
                  <span class="compare-val">{{ currentDuplicateFile?.uploadTime }}</span>
                </div>
              </div>
            </div>

            <div class="compare-vs">
              <div class="vs-badge">
                <span>相似度</span>
                <strong>{{ currentDuplicateFile?.similarity }}%</strong>
              </div>
            </div>

            <div class="compare-col">
              <div class="compare-label existing-label">
                <Copy :size="14" />
                <span>已有文件</span>
              </div>
              <div class="compare-content">
                <div class="compare-item">
                  <span class="compare-key">文件名</span>
                  <span class="compare-val">临时用地批复_扫描件.pdf</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">文件哈希</span>
                  <span class="compare-val hash">SHA256: f6a1b2c3d4e5...</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">文件大小</span>
                  <span class="compare-val">3.20MB</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">资料周期</span>
                  <span class="compare-val">2026年度</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">上传时间</span>
                  <span class="compare-val">2026-03-20 11:00</span>
                </div>
                <div class="compare-item">
                  <span class="compare-key">已关联任务</span>
                  <span class="compare-val task-list">临时用地合规资料</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-btn secondary" @click="handleCancelUpload">取消上传</button>
          <button class="modal-btn" @click="handleConfirmDifferent">确认为不同资料</button>
          <button class="modal-btn" @click="handleUploadAsNewVersion">作为新版本上传</button>
          <button class="modal-btn primary" @click="handleReuseExisting">复用已有资料</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-smart-upload {
  min-height: 0;
}

.upload-buttons .ws-btn,
.recommend-actions .ws-btn {
  flex: 1;
}

.main-content {
  display: flex;
  gap: 10px;
  flex: 1;
  overflow: hidden;
}

.left-section {
  width: 60%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-x: hidden;
  overflow-y: auto;
  min-height: 0;
}

.right-section {
  width: 40%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.hidden-file-input {
  display: none;
}

.upload-section {
  flex-shrink: 0;
}

.upload-area {
  border: 2px dashed rgba(105, 227, 111, 0.3);
  border-radius: 8px;
  padding: 10px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #69e36f;
  background: rgba(105, 227, 111, 0.05);
}

.upload-icon {
  color: #69e36f;
  margin-bottom: 4px;
  display: flex;
  justify-content: center;
}

.upload-text {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
}

.upload-desc {
  font-size: 11px;
  color: #8fa9c8;
  margin-top: 6px;
  line-height: 1.4;
  text-align: center;
}

.upload-buttons {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.upload-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.upload-btn.primary {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  color: #031020;
  font-weight: 600;
}

.parse-queue-section {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.parse-queue-section > .ws-pagination-bar {
  border: 1px solid rgba(47, 156, 255, 0.14);
  border-radius: 0 0 8px 8px;
}

.queue-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  flex-shrink: 0;
}

.status-tabs {
  display: flex;
  gap: 2px;
  flex-wrap: wrap;
}

.status-tab {
  padding: 2px 8px;
  font-size: 12px;
  color: #8fa9c8;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  border: 1px solid transparent;
}

.status-tab:hover {
  color: #2f9cff;
}

.status-tab.active {
  color: #2f9cff;
  background: rgba(47, 156, 255, 0.1);
  border-color: rgba(47, 156, 255, 0.3);
}

.queue-search {
  margin-left: auto;
  width: 180px;
  flex-shrink: 0;
}

.queue-actions {
  display: flex;
  gap: 8px;
}

.queue-table {
  border: none;
  border-radius: 0;
  background: transparent;
  flex: 1;
  min-height: 0;
}

.col-checkbox {
  width: 40px;
}

.col-file {
  width: auto;
}

.col-file .file-icon {
  color: #8fa9c8;
  flex-shrink: 0;
  vertical-align: middle;
  margin-right: 8px;
}

.file-name-text {
  vertical-align: middle;
}

.col-size {
  width: 80px;
  color: #8fa9c8;
  font-size: 12px;
}

.col-progress {
  width: 140px;
}

.col-status {
  width: 100px;
}

.col-time {
  width: 176px;
  color: #8fa9c8;
  font-size: 12px;
}

.col-action {
  width: 168px;
}

.col-action .ws-btn + .ws-btn {
  margin-left: 4px;
}

.empty-row {
  text-align: center;
  color: #5a7a9a;
  padding: 40px !important;
  font-size: 12px;
}

.ai-summary-card {
  flex-shrink: 0;
}

.ai-recommend-card {
  flex: 1;
  min-height: 0;
}

.detail-btn {
  font-size: 12px;
  color: #69e36f;
  background: transparent;
  border: none;
  cursor: pointer;
}

.summary-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.parse-source-badge {
  font-size: 11px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(105, 227, 111, 0.1);
  border-radius: 4px;
  padding: 2px 8px;
  white-space: nowrap;
}

.parse-empty-hint {
  font-size: 12px;
  color: #8fa9c8;
  line-height: 1.5;
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.15);
}

.extracted-metrics {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(143, 169, 200, 0.15);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.extracted-metrics-title {
  font-size: 12px;
  color: #8fa9c8;
  margin-bottom: 2px;
}

.extracted-metric-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 8px;
  align-items: center;
  font-size: 12px;
}

.metric-name {
  color: #8fa9c8;
}

.metric-value {
  color: #e8f3ff;
  font-weight: 600;
}

.metric-conf {
  color: #69e36f;
  min-width: 36px;
  text-align: right;
}

.ai-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.field-label {
  font-size: 12px;
  color: #8fa9c8;
  flex-shrink: 0;
  width: 90px;
}

.field-value {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  text-align: right;
}

.field-value-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  position: relative;
}

.field-value-wrap:hover .edit-hint {
  opacity: 1;
}

.edit-hint {
  font-size: 10px;
  color: #5a7a9a;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.field-edit {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.edit-input {
  width: 180px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 13px;
  outline: none;
  text-align: right;
}

.edit-input:focus {
  border-color: #69e36f;
}

.link-like {
  color: #2f9cff;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.kpi-value {
  display: flex;
  align-items: center;
  gap: 6px;
}

.kpi-code {
  padding: 2px 6px;
  background: rgba(47, 156, 255, 0.15);
  color: #2f9cff;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
}

.confidence-field .field-value {
  flex: 1;
}

.confidence-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

.confidence-bar {
  width: 100px;
  height: 6px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 3px;
}

.confidence-text {
  font-size: 12px;
  color: #69e36f;
  font-weight: 600;
  width: 40px;
  text-align: right;
}

.duplicate-warning {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 179, 71, 0.08);
  border: 1px solid rgba(255, 179, 71, 0.3);
  border-radius: 8px;
  margin-top: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.duplicate-warning:hover {
  background: rgba(255, 179, 71, 0.12);
}

.warning-icon {
  color: #ffb347;
  flex-shrink: 0;
}

.warning-text {
  font-size: 13px;
  color: #ffb347;
  font-weight: 600;
}

.warning-count {
  font-size: 14px;
  color: #ffb347;
  font-weight: 700;
}

.warning-btn-text {
  margin-left: auto;
  font-size: 12px;
  color: #ffb347;
}

.rec-count {
  font-size: 12px;
  color: #5a7a9a;
}

.recommend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: visible;
  flex: 0 0 auto;
}

.recommend-item {
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(105, 227, 111, 0.08);
  border-radius: 8px;
  flex: 0 0 auto;
}

.basis-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recommend-file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
}

.recommend-file-name span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recommend-file-icon {
  color: #69e36f;
  flex-shrink: 0;
}

.recommend-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.match-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid;
  background: rgba(105, 227, 111, 0.08);
}

.reuse-count {
  font-size: 11px;
  color: #8fa9c8;
}

.recommend-basis {
  display: flex;
  gap: 4px;
  margin-bottom: 10px;
  line-height: 1.5;
}

.basis-label {
  font-size: 11px;
  color: #5a7a9a;
  flex-shrink: 0;
}

.basis-text {
  font-size: 11px;
  color: #8fa9c8;
}

.recommend-actions {
  display: flex;
  gap: 8px;
}

.rec-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.rec-btn:hover {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.rec-btn.primary {
  background: rgba(105, 227, 111, 0.2);
  color: #69e36f;
  font-weight: 600;
  border: 1px solid #69e36f;
}

.rec-btn.ghost {
  background: rgba(47, 156, 255, 0.08);
  border-color: rgba(47, 156, 255, 0.25);
  color: #7fb6ef;
}

.rec-btn.ghost:hover {
  background: rgba(47, 156, 255, 0.16);
  color: #9ec8f5;
}

.rec-pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  margin-top: 10px;
  border-top: 1px solid rgba(105, 227, 111, 0.08);
  flex-shrink: 0;
}

.rec-pagination-info {
  font-size: 11px;
  color: #5a7a9a;
}

.rec-pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rec-page-btn {
  padding: 3px 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 3px;
  color: #e8f3ff;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.rec-page-btn:hover:not(:disabled) {
  border-color: #69e36f;
  color: #69e36f;
}

.rec-page-btn.active {
  background: rgba(105, 227, 111, 0.2);
  border-color: #69e36f;
  color: #69e36f;
}

.rec-page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: rgba(5, 26, 50, 0.98);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 10px;
  width: 720px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.modal-title {
  font-size: 15px;
  font-weight: 600;
  color: #e8f3ff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-title-icon {
  color: #ffb347;
}

.modal-close {
  background: none;
  border: none;
  color: #8fa9c8;
  font-size: 24px;
  cursor: pointer;
  line-height: 1;
  padding: 0 4px;
}

.modal-close:hover {
  color: #e8f3ff;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.duplicate-compare {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.compare-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.compare-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 6px 6px 0 0;
  font-size: 13px;
  font-weight: 600;
}

.new-label {
  background: rgba(47, 156, 255, 0.15);
  color: #2f9cff;
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-bottom: none;
}

.existing-label {
  background: rgba(166, 108, 255, 0.15);
  color: #a66cff;
  border: 1px solid rgba(166, 108, 255, 0.3);
  border-bottom: none;
}

.compare-content {
  flex: 1;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(105, 227, 111, 0.08);
  border-radius: 0 0 6px 6px;
}

.compare-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid rgba(105, 227, 111, 0.05);
  gap: 12px;
}

.compare-item:last-child {
  border-bottom: none;
}

.compare-key {
  font-size: 12px;
  color: #8fa9c8;
  flex-shrink: 0;
}

.compare-val {
  font-size: 12px;
  color: #e8f3ff;
  text-align: right;
  word-break: break-all;
}

.compare-val.hash {
  font-family: monospace;
  font-size: 11px;
  color: #8fa9c8;
}

.compare-val.task-list {
  color: #2f9cff;
}

.compare-vs {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 80px;
}

.vs-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(255, 179, 71, 0.1);
  border: 1px solid rgba(255, 179, 71, 0.3);
  border-radius: 8px;
}

.vs-badge span {
  font-size: 11px;
  color: #ffb347;
}

.vs-badge strong {
  font-size: 18px;
  color: #ffb347;
  font-weight: 700;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid rgba(105, 227, 111, 0.1);
}

.modal-btn {
  padding: 8px 18px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn:hover {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.modal-btn.primary {
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  color: #031020;
  font-weight: 600;
  border: none;
}

.modal-btn.secondary {
  background: rgba(255, 79, 94, 0.08);
  border-color: rgba(255, 79, 94, 0.2);
  color: #ff8a96;
}

.modal-btn.secondary:hover {
  background: rgba(255, 79, 94, 0.15);
}
</style>
