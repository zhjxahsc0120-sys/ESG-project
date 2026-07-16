<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Upload, FolderOpen, Link2, FileText, FileImage, FileSpreadsheet, AlertTriangle } from 'lucide-vue-next'
import {
  parseQueue as mockParseQueue,
  aiParseResult as mockAiParseResult,
  suggestedTasks as mockSuggestedTasks,
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
import type { ParseQueueItem, AiParseResult, SuggestedTask } from '@/types/workspace'
import type { ParseFieldItem, MatchCandidateItem, ParseJobDetail } from '@/services/api'
import { emitWorkspaceRefresh, onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const showUploadArea = ref(true)
const selectedTasks = ref<string[]>(['st1', 'st2'])
const parseQueueList = ref<ParseQueueItem[]>([...mockParseQueue])
const aiParseResult = ref<AiParseResult>({ ...mockAiParseResult })
const suggestedTasks = ref<SuggestedTask[]>([...mockSuggestedTasks])
const fileInputRef = ref<HTMLInputElement | null>(null)

const currentFileId = ref<number | null>(null)
const currentJobId = ref<number | null>(null)
const currentJob = ref<ParseJobDetail | null>(null)
const pageMessage = ref('')
const pageMessageType = ref<'success' | 'error' | 'info'>('info')

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
    updateAiResultFromFields(fieldsRes.items)
  }
  if (candidatesRes && candidatesRes.items.length > 0) {
    updateCandidatesFromApi(candidatesRes.items, currentJob.value?.fileName || '')
  }
}

function updateAiResultFromFields(fields: ParseFieldItem[]) {
  const map: Record<string, string> = {}
  for (const f of fields) {
    map[f.fieldKey] = f.fieldValue
  }
  const module = (map['esg_module'] || map['module'] || aiParseResult.value.module) as 'E' | 'S' | 'G'
  aiParseResult.value = {
    documentType: map['document_type'] || aiParseResult.value.documentType,
    cycle: map['period'] || aiParseResult.value.cycle,
    module,
    moduleName: module === 'E' ? '环境环保' : module === 'S' ? '社会责任' : module === 'G' ? '治理合规' : aiParseResult.value.moduleName,
    responsibilityUnit: map['responsibility_unit'] || aiParseResult.value.responsibilityUnit,
    validPeriod: aiParseResult.value.validPeriod,
    duplicateCount: aiParseResult.value.duplicateCount,
    duplicateTip: aiParseResult.value.duplicateTip,
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
      showMessage(`解析任务已创建。JobID：${parseRes.jobId}`, 'success')
      await loadData()
      await loadJobDetails(parseRes.jobId)
    }
  } else {
    showMessage('上传接口未响应，保留 mock 数据。', 'error')
  }
  input.value = ''
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
  showMessage('保存到资料中心为原型预留操作；如需真实入库，请使用“确认入库并关联”。', 'info')
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
    showMessage('AI解析详情为原型展示；当前未接入真实 AI/OCR 能力。', 'info')
    return
  }
  loadJobDetails(currentJobId.value)
}

function handleViewDuplicateDetail() {
  showMessage('重复检测为原型展示；当前未接入真实文件哈希比对能力。', 'info')
}

function handleViewFile(fileName: string) {
  showMessage(`文件预览为原型展示，未接入真实文件存储服务。文件：${fileName}`, 'info')
}

function handleViewLink(taskName: string) {
  showMessage(`查看关联详情为原型展示。任务：${taskName}`, 'info')
}

async function handleViewResult(item: ParseQueueItem) {
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
    default: return '#8fa9c8'
  }
}

function isSelected(taskId: string) {
  return selectedTasks.value.includes(taskId)
}

function getFileIcon(fileName: string) {
  if (fileName.endsWith('.pdf')) return FileText
  if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls')) return FileSpreadsheet
  if (fileName.endsWith('.jpg') || fileName.endsWith('.png') || fileName.endsWith('.jpeg')) return FileImage
  return FileText
}

function getQueueButtonAction(status: string): string {
  if (status === '解析完成' || status === '已入库' || status === '待确认') return '查看结果'
  if (status.includes('匹配中') || status.includes('解析中')) return '查看进度'
  if (status.includes('失败')) return '查看原因'
  return '查看'
}
</script>

<template>
  <div class="workspace-smart-upload">
    <div class="page-header">
      <div class="page-title">ESG智能入库</div>
    </div>

    <div class="main-content">
      <div class="left-section">
        <div class="upload-section">
          <input
            ref="fileInputRef"
            class="hidden-file-input"
            type="file"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.zip,.rar"
            @change="handleFileChange"
          />
          <div class="section-header">
            <div class="section-title">上传资料</div>
            <div class="section-desc">支持 PDF、Word、Excel、图片、压缩包等格式，单个文件最大 200MB</div>
          </div>
          
          <div class="upload-area" @click="handleSelectFile">
            <div class="upload-icon">
              <Upload :size="36" />
            </div>
            <div class="upload-text">将文件拖拽到此处，或选择文件上传</div>
            <div class="upload-subtext">一次上传，智能解析，支持多任务复用</div>
          </div>

          <div class="upload-buttons">
            <button class="upload-btn primary" @click="handleSelectFile">
              <Upload :size="16" />
              <span>选择文件</span>
            </button>
            <button class="upload-btn" @click="handleBatchImport">
              <FolderOpen :size="16" />
              <span>批量导入</span>
            </button>
            <button class="upload-btn" @click="handleSelectFromCenter">
              <Link2 :size="16" />
              <span>从资料中心选择</span>
            </button>
          </div>

          <div class="parse-queue">
            <div class="queue-header">
              <span class="queue-title">解析队列（{{ parseQueueList.length }}）</span>
            </div>
            <div class="queue-list">
              <div v-for="item in parseQueueList" :key="item.id" class="queue-item">
                <div class="file-info">
                  <component :is="getFileIcon(item.fileName)" :size="16" class="file-icon" />
                  <span class="file-name">{{ item.fileName }}</span>
                </div>
                <span class="file-size">{{ item.size }}</span>
                <div class="progress-wrapper">
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: `${item.progress}%` }"></div>
                  </div>
                  <span class="progress-text">{{ item.progress }}%</span>
                </div>
                <span :class="['queue-status', { completed: item.status === '解析完成' || item.status === '已入库' }]">{{ item.status }}</span>
                <button class="action-btn" :class="{ primary: getQueueButtonAction(item.status) === '查看结果' }" @click.stop="handleViewResult(item)">{{ getQueueButtonAction(item.status) }}</button>
              </div>
            </div>
          </div>
        </div>

        <div class="suggested-section">
          <div class="section-header">
            <div class="section-title">建议关联任务</div>
            <span class="section-tip">同一资料只入库一次，可服务多个流程</span>
          </div>
          <div class="suggested-table-wrapper">
            <table class="suggested-table">
              <thead>
                <tr>
                  <th class="checkbox-col">
                    <input type="checkbox" :checked="selectedTasks.length === suggestedTasks.length" @change="selectedTasks = selectedTasks.length === suggestedTasks.length ? [] : suggestedTasks.map(t => t.id)" />
                  </th>
                  <th>资料名称</th>
                  <th>建议关联任务</th>
                  <th>所属模块</th>
                  <th>匹配度</th>
                  <th>复用情况</th>
                  <th>确认状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="task in suggestedTasks" :key="task.id">
                  <td class="checkbox-col">
                    <input type="checkbox" :checked="isSelected(task.id)" @change="toggleTaskSelect(task.id)" />
                  </td>
                  <td class="doc-name">
                    <component :is="getFileIcon(task.documentName)" :size="14" class="doc-icon" />
                    {{ task.documentName }}
                  </td>
                  <td>{{ task.taskName }}</td>
                  <td>
                    <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                      {{ task.module }} {{ task.moduleName }}
                    </span>
                  </td>
                  <td>
                    <div class="match-bar">
                      <div class="match-fill" :style="{ width: `${task.matchRate}%` }"></div>
                    </div>
                    <span class="match-text">{{ task.matchRate }}%</span>
                  </td>
                  <td>{{ task.reuseCount === 0 ? '未复用' : `已复用 ${task.reuseCount} 次` }}</td>
                  <td>
                    <span class="status-tag" :style="{ color: getStatusColor(task.confirmStatus) }">
                      {{ task.confirmStatus }}
                    </span>
                  </td>
                  <td>
                    <button class="link-btn" v-if="task.confirmStatus !== '已关联'" @click="handleConfirmAndLink">确认关联</button>
                    <button class="view-btn" v-else @click="handleViewLink(task.taskName)">查看关联</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="right-section">
        <div class="ai-summary-card">
          <div class="card-header">
            <div class="card-title">AI 解析摘要</div>
            <button class="detail-btn" @click="handleViewParseDetail">查看解析详情</button>
          </div>
          <div class="ai-fields">
            <div class="ai-field">
              <span class="field-label">资料类型</span>
              <span class="field-value">{{ aiParseResult.documentType }}</span>
            </div>
            <div class="ai-field">
              <span class="field-label">资料周期</span>
              <span class="field-value">{{ aiParseResult.cycle }}</span>
            </div>
            <div class="ai-field">
              <span class="field-label">所属模块</span>
              <span class="field-value" :style="{ color: getModuleColor(aiParseResult.module) }">
                {{ aiParseResult.module }} {{ aiParseResult.moduleName }}
              </span>
            </div>
            <div class="ai-field">
              <span class="field-label">责任单位</span>
              <span class="field-value">{{ aiParseResult.responsibilityUnit }}</span>
            </div>
            <div class="ai-field">
              <span class="field-label">有效期</span>
              <span class="field-value">{{ aiParseResult.validPeriod }}</span>
            </div>
          </div>

          <div class="duplicate-warning" v-if="aiParseResult.duplicateCount > 0">
            <AlertTriangle :size="16" class="warning-icon" />
            <span class="warning-text">疑似重复</span>
            <span class="warning-count">{{ aiParseResult.duplicateCount }}份</span>
            <button class="warning-btn" @click="handleViewDuplicateDetail">查看重复详情</button>
          </div>

          <div class="ai-tip">
            <div class="tip-header">
              <span class="tip-icon">AI</span>
              <span class="tip-title">AI提示</span>
            </div>
            <p class="tip-content">{{ aiParseResult.duplicateTip }}</p>
          </div>
        </div>

        <div class="ai-recommend-card">
          <div class="card-header">
            <div class="card-title">AI 智能推荐</div>
          </div>
          <div class="recommend-file">
            <FileText :size="24" class="file-icon" />
            <div class="file-info">
              <span class="file-name">弃渣场巡查记录_2026-07.pdf</span>
              <span class="match-rate">匹配度：96%</span>
            </div>
          </div>
          <div class="recommend-text">该资料已用于其他流程，无需重复上传</div>
          <div class="recommend-actions">
            <button class="action-btn primary" @click="handleConfirmAndLink">确认关联</button>
            <button class="action-btn" @click="handleViewFile('弃渣场巡查记录_2026-07.pdf')">查看文件</button>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-actions">
      <button class="cancel-btn" @click="handleCancel">取消</button>
      <button class="save-btn" @click="handleSaveToCenter">保存到资料中心</button>
      <button class="confirm-btn" @click="handleConfirmAndLink">确认入库并关联</button>
    </div>
  </div>
</template>

<style scoped>
.workspace-smart-upload {
  padding: 20px;
  height: calc(100% - 120px);
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8f3ff;
}

.page-message {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
}

.page-message.info {
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.18);
  color: #9fc7ff;
}

.page-message.success {
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  color: #69e36f;
}

.page-message.error {
  background: rgba(255, 79, 94, 0.08);
  border: 1px solid rgba(255, 79, 94, 0.2);
  color: #ff8a96;
}

.main-content {
  display: flex;
  gap: 20px;
  flex: 1;
  overflow-y: auto;
}

.left-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.right-section {
  width: 380px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-section, .suggested-section {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.hidden-file-input {
  display: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.section-desc {
  font-size: 12px;
  color: #8fa9c8;
  margin-top: 4px;
}

.section-tip {
  font-size: 11px;
  color: #5a7a9a;
}

.upload-area {
  border: 2px dashed rgba(105, 227, 111, 0.3);
  border-radius: 10px;
  padding: 40px;
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
  margin-bottom: 12px;
}

.upload-text {
  font-size: 14px;
  color: #e8f3ff;
  font-weight: 500;
}

.upload-subtext {
  font-size: 12px;
  color: #8fa9c8;
  margin-top: 6px;
}

.upload-buttons {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.upload-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 8px;
  color: #8fa9c8;
  font-size: 13px;
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

.parse-queue {
  margin-top: 16px;
}

.queue-header {
  margin-bottom: 12px;
}

.queue-title {
  font-size: 12px;
  color: #8fa9c8;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.file-icon {
  color: #8fa9c8;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.file-name {
  font-size: 12px;
  color: #e8f3ff;
}

.file-size {
  font-size: 11px;
  color: #5a7a9a;
  width: 80px;
}

.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 120px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 3px;
}

.progress-text {
  font-size: 11px;
  color: #8fa9c8;
  width: 35px;
}

.queue-status {
  font-size: 11px;
  color: #ffb347;
  width: 80px;
}

.queue-status.completed {
  color: #69e36f;
}

.action-btn {
  padding: 4px 10px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 11px;
  cursor: pointer;
}

.action-btn.primary {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.suggested-table-wrapper {
  overflow-x: auto;
}

.suggested-table {
  width: 100%;
  border-collapse: collapse;
}

.suggested-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.checkbox-col {
  width: 40px;
}

.suggested-table td {
  padding: 10px 12px;
  font-size: 12px;
  color: #e8f3ff;
  border-bottom: 1px solid rgba(105, 227, 111, 0.05);
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  color: #8fa9c8;
}

.module-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status-tag {
  font-size: 11px;
  font-weight: 500;
}

.match-bar {
  width: 60px;
  height: 6px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.match-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 3px;
}

.match-text {
  margin-left: 8px;
  font-size: 11px;
  color: #8fa9c8;
}

.link-btn {
  padding: 4px 10px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 4px;
  color: #69e36f;
  font-size: 11px;
  cursor: pointer;
}

.view-btn {
  padding: 4px 10px;
  background: rgba(105, 227, 111, 0.05);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 11px;
  cursor: pointer;
}

.ai-summary-card, .ai-recommend-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.detail-btn {
  font-size: 12px;
  color: #69e36f;
  background: transparent;
  border: none;
  cursor: pointer;
}

.ai-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-label {
  font-size: 12px;
  color: #8fa9c8;
}

.field-value {
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
}

.duplicate-warning {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  border-radius: 8px;
  margin-top: 16px;
}

.warning-icon {
  color: #ff4f5e;
}

.warning-text {
  font-size: 12px;
  color: #ff4f5e;
  font-weight: 600;
}

.warning-count {
  font-size: 14px;
  color: #ff4f5e;
  font-weight: 700;
}

.warning-btn {
  margin-left: auto;
  padding: 4px 10px;
  background: rgba(255, 79, 94, 0.15);
  border: 1px solid rgba(255, 79, 94, 0.3);
  border-radius: 4px;
  color: #ff4f5e;
  font-size: 11px;
  cursor: pointer;
}

.ai-tip {
  margin-top: 16px;
  padding: 12px;
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.2);
  border-radius: 8px;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.tip-icon {
  padding: 2px 6px;
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #031020;
}

.tip-title {
  font-size: 12px;
  color: #2f9cff;
  font-weight: 500;
}

.tip-content {
  font-size: 11px;
  color: #8fa9c8;
  margin: 0;
  line-height: 1.5;
}

.recommend-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
}

.recommend-file .file-icon {
  color: #69e36f;
}

.recommend-file .file-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
}

.match-rate {
  font-size: 11px;
  color: #69e36f;
}

.recommend-text {
  font-size: 12px;
  color: #8fa9c8;
  margin-top: 12px;
}

.recommend-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.recommend-actions .action-btn {
  flex: 1;
  padding: 10px;
  font-size: 12px;
}

.recommend-actions .action-btn.primary {
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  color: #031020;
  font-weight: 600;
  border: none;
}

.bottom-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(105, 227, 111, 0.1);
  margin-top: 16px;
}

.cancel-btn {
  padding: 10px 24px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 13px;
  cursor: pointer;
}

.save-btn {
  padding: 10px 24px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 6px;
  color: #69e36f;
  font-size: 13px;
  cursor: pointer;
}

.confirm-btn {
  padding: 10px 24px;
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border: none;
  border-radius: 6px;
  color: #031020;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
</style>
