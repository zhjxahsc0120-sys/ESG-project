<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Upload, FolderOpen, Send, ChevronLeft, ChevronRight, Layers, Sparkles } from 'lucide-vue-next'
import {
  workspaceStatusCards as mockWorkspaceStatusCards,
  allUploadTasks,
  todayFocusList,
  quickQuestions,
} from '@/data/workspace.mock'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { TASK_STATUS_COLORS, MODULE_COLORS, STATUS_TO_NEXT_STEP } from '@/types/workspace'

const emit = defineEmits<{
  (e: 'navigate', key: string, status?: string): void
  (e: 'openTask', taskId: string): void
}>()

const inputValue = ref('')
const assistantMessage = ref('')
const currentPage = ref(1)
const pageSize = 10
const taskList = ref<UploadTask[]>([...allUploadTasks])
const statusCards = ref<StatusCard[]>([...mockWorkspaceStatusCards])
const showAssistantResult = ref(false)
const assistantResultTasks = ref<UploadTask[]>([])

function handleStatusCardClick(label: string) {
  let status = ''
  if (label === '当前待办') status = 'todo'
  else if (label === '待上传') status = '待上传'
  else if (label === '待补正') status = '待补正'
  else if (label === '待提交') status = '待提交'
  else if (label === '审核中') status = '审核中'
  else if (label === '已完成') status = '已完成'
  emit('navigate', 'tasks', status)
}

function handleUploadClick() {
  emit('navigate', 'smart-upload')
}

function handleBatchImport() {
  emit('navigate', 'smart-upload')
}

function handleReuseFromLibrary() {
  emit('navigate', 'documents')
}

function handleTaskClick(taskId: string) {
  emit('openTask', taskId)
}

function handleQuickQuestion(question: string) {
  inputValue.value = question
  showAssistantResult.value = true

  if (question.includes('今天') || question.includes('必须提交')) {
    assistantResultTasks.value = taskList.value.filter(t =>
      t.status === '待提交' || t.isUrgent
    ).slice(0, 5)
  } else if (question.includes('逾期')) {
    assistantResultTasks.value = taskList.value.filter(t => t.isOverdue).slice(0, 5)
  } else if (question.includes('退回') || question.includes('补正')) {
    assistantResultTasks.value = taskList.value.filter(t =>
      t.status === '待补正' || t.status === '已退回'
    ).slice(0, 5)
  } else if (question.includes('月报')) {
    assistantResultTasks.value = taskList.value.filter(t =>
      t.relatedReport?.includes('7月') && t.status !== '已完成' && t.status !== '已归档'
    ).slice(0, 5)
  }
}

function handleSend() {
  if (!inputValue.value.trim()) return
  showAssistantResult.value = true
  assistantResultTasks.value = taskList.value.slice(0, 3)
}

function getModuleColor(module: string) {
  return MODULE_COLORS[module] || '#8fa9c8'
}

function getStatusColor(status: string) {
  return TASK_STATUS_COLORS[status] || '#8fa9c8'
}

function getSourceDisplay(task: UploadTask): string {
  if (task.sourceType === 'KPI指标' && task.sourceKpiCode) {
    return `${task.sourceKpiCode}｜${task.sourceKpiName || ''}`
  }
  if (task.sourceType === '月报任务') {
    return task.relatedReport || task.sourceName || '月报任务'
  }
  if (task.sourceType === '审核补正') {
    return '审核退回补正'
  }
  return task.sourceName || task.sourceType || '周期任务'
}

const statusPriority: Record<string, number> = {
  '已逾期': 0,
  '待补正_urgent': 1,
  '月报_待提交': 2,
  '待上传': 3,
  '待补正': 4,
  '待提交': 5,
  '审核中': 6,
}

function getTaskPriority(task: UploadTask): number {
  if (task.isOverdue) return statusPriority['已逾期']
  if (task.status === '待补正' && task.isUrgent) return statusPriority['待补正_urgent']
  if (task.relatedReport && task.status === '待提交') return statusPriority['月报_待提交']
  return statusPriority[task.status] ?? 9
}

const sortedTasks = computed(() => {
  return [...taskList.value].sort((a, b) => {
    const aPriority = getTaskPriority(a)
    const bPriority = getTaskPriority(b)
    if (aPriority !== bPriority) return aPriority - bPriority
    return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
  })
})

const displayTasks = computed(() => {
  return sortedTasks.value.slice(0, 10)
})

function getFocusTypeClass(type: string) {
  switch (type) {
    case 'overdue': return 'overdue'
    case 'urgent': return 'urgent'
    case 'today': return 'today'
    default: return 'normal'
  }
}

function handleFocusClick(focusId: string) {
  emit('openTask', focusId)
}
</script>

<template>
  <div class="workspace-home">
    <div class="main-content">
      <div class="ws-page-header">
        <div class="ws-page-title-group">
          <div class="ws-page-title">工作台首页</div>
          <div class="ws-page-subtitle">查看待办任务、上传资料与重点提醒</div>
        </div>
      </div>
      <div class="ws-status-cards cols-6">
        <div
          v-for="card in statusCards"
          :key="card.label"
          class="ws-status-card"
          :style="{ '--accent-color': card.color }"
          @click="handleStatusCardClick(card.label)"
        >
          <span class="ws-card-label">{{ card.label }}</span>
          <div class="ws-card-value-row">
            <span class="ws-card-value">{{ card.value }}</span>
            <span class="ws-card-unit">{{ card.unit }}</span>
          </div>
        </div>
      </div>

      <div class="smart-upload-section">
        <div class="smart-upload-left">
          <div class="section-title">
            <Sparkles :size="16" class="title-icon" />
            <span>ESG 智能入库</span>
          </div>
          <div class="section-subtitle">上传后自动识别资料类型、所属周期、关联指标和待办任务</div>
        </div>
        <div class="upload-buttons">
          <button class="upload-btn primary" @click="handleUploadClick">
            <Upload :size="16" />
            <span>上传文件</span>
          </button>
          <button class="upload-btn" @click="handleBatchImport">
            <FolderOpen :size="16" />
            <span>批量导入</span>
          </button>
          <button class="upload-btn" @click="handleReuseFromLibrary">
            <Layers :size="16" />
            <span>从资料中心复用</span>
          </button>
        </div>
      </div>

      <div class="tasks-section">
        <div class="section-header">
          <div class="section-title">我的上传任务</div>
          <div class="section-more" @click="emit('navigate', 'tasks')">查看全部 →</div>
        </div>
        <div class="ws-table-container">
          <div class="ws-table-header-wrapper">
            <table class="ws-table">
              <colgroup>
                <col style="width: 22%" />
                <col style="width: 24%" />
                <col style="width: 10%" />
                <col style="width: 14%" />
                <col style="width: 14%" />
                <col style="width: 10%" />
                <col style="width: 10%" />
              </colgroup>
              <thead>
                <tr>
                  <th>任务名称</th>
                  <th>来源/关联事项</th>
                  <th>ESG模块</th>
                  <th>截止时间</th>
                  <th>资料进度</th>
                  <th>状态</th>
                  <th>下一步</th>
                </tr>
              </thead>
            </table>
          </div>
          <div class="ws-table-body-wrapper no-scroll">
            <table class="ws-table">
              <colgroup>
                <col style="width: 22%" />
                <col style="width: 24%" />
                <col style="width: 10%" />
                <col style="width: 14%" />
                <col style="width: 14%" />
                <col style="width: 10%" />
                <col style="width: 10%" />
              </colgroup>
              <tbody>
                <tr
                  v-for="task in displayTasks"
                  :key="task.id"
                  @click="handleTaskClick(task.id)"
                >
                  <td class="task-name">{{ task.name }}</td>
                  <td class="task-source">{{ getSourceDisplay(task) }}</td>
                  <td>
                    <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                      {{ task.module }} {{ task.moduleName }}
                    </span>
                  </td>
                  <td :class="{ 'overdue': task.isOverdue }">{{ task.deadlineDisplay }}</td>
                  <td>
                    <div class="progress-cell">
                      <div class="progress-bar">
                        <div class="progress-fill" :style="{ width: `${(task.progressCurrent / task.progressTotal) * 100}%` }"></div>
                      </div>
                      <span class="progress-text">{{ task.progressCurrent }}/{{ task.progressTotal }}</span>
                    </div>
                  </td>
                  <td>
                    <span class="status-tag" :style="{ background: `${getStatusColor(task.status)}20`, color: getStatusColor(task.status) }">
                      {{ task.status }}
                    </span>
                  </td>
                  <td>
                    <button class="next-step-btn" @click.stop="handleTaskClick(task.id)">
                      {{ task.nextStep }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <aside class="right-sidebar">
      <div class="assistant-card">
        <div class="card-header">
          <div class="card-title">
            <Sparkles :size="14" class="title-icon" />
            <span>ESG 智能助手</span>
          </div>
        </div>
        <div class="input-wrapper">
          <input
            v-model="inputValue"
            type="text"
            placeholder="询问待办任务、缺失资料或上传要求"
            class="assistant-input"
            @keyup.enter="handleSend"
          />
          <button class="send-btn" @click="handleSend">
            <Send :size="15" />
          </button>
        </div>
        <div v-if="showAssistantResult && assistantResultTasks.length > 0" class="assistant-result">
          <div class="result-title">查询结果</div>
          <div
            v-for="task in assistantResultTasks"
            :key="task.id"
            class="result-item"
            @click="handleTaskClick(task.id)"
          >
            <span class="result-name">{{ task.name }}</span>
            <span class="result-status" :style="{ color: getStatusColor(task.status) }">{{ task.status }}</span>
          </div>
        </div>
        <div class="quick-questions">
          <div class="quick-title">快捷问题</div>
          <button
            v-for="q in quickQuestions"
            :key="q.id"
            class="quick-question-btn"
            @click="handleQuickQuestion(q.question)"
          >
            {{ q.question }}
          </button>
        </div>
      </div>

      <div class="focus-card">
        <div class="card-header">
          <div class="card-title">今日重点关注</div>
          <div class="card-count">{{ todayFocusList.length }} 条</div>
        </div>
        <div class="focus-list">
          <div
            v-for="item in todayFocusList"
            :key="item.id"
            class="focus-item"
            :class="getFocusTypeClass(item.type)"
            @click="handleFocusClick(item.id)"
          >
            <div class="focus-main">
              <span class="focus-name">{{ item.name }}</span>
              <span v-if="item.status" class="focus-status">{{ item.status }}</span>
            </div>
            <span class="focus-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.workspace-home {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(420px, 26vw, 480px);
  gap: 16px;
  padding: 14px 16px;
  height: 100%;
  box-sizing: border-box;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.smart-upload-section {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 12px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
  box-sizing: border-box;
}

.smart-upload-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-icon {
  color: #69e36f;
  margin-right: 6px;
  flex-shrink: 0;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.section-subtitle {
  font-size: 11px;
  color: #8fa9c8;
  line-height: 1.4;
}

.upload-buttons {
  display: flex;
  gap: 10px;
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(105, 227, 111, 0.06);
  border: 1px solid rgba(105, 227, 111, 0.18);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.upload-btn:hover {
  background: rgba(105, 227, 111, 0.12);
  color: #69e36f;
}

.upload-btn.primary {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  color: #031020;
  font-weight: 600;
}

.upload-btn.primary:hover {
  opacity: 0.9;
}

.tasks-section {
  flex: 1;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.08);
  border-radius: 8px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-more {
  font-size: 12px;
  color: #2f9cff;
  cursor: pointer;
  transition: color 0.2s;
}

.section-more:hover {
  color: #69e36f;
}

.task-name {
  font-weight: 500;
}

.task-source {
  color: #8fa9c8;
  font-size: 12px;
}

.module-tag, .status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 5px;
  background: rgba(105, 227, 111, 0.08);
  border-radius: 3px;
  overflow: hidden;
  min-width: 50px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 3px;
}

.progress-text {
  font-size: 11px;
  color: #8fa9c8;
  flex-shrink: 0;
}

.next-step-btn {
  padding: 5px 12px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.25);
  border-radius: 4px;
  color: #69e36f;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.next-step-btn:hover {
  background: rgba(105, 227, 111, 0.18);
}

.overdue {
  color: #ff4f5e;
}

.assistant-card, .focus-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.card-title .title-icon {
  color: #69e36f;
  margin-right: 6px;
}

.card-count {
  font-size: 11px;
  color: #5a7a9a;
}

.input-wrapper {
  display: flex;
  gap: 6px;
  margin-bottom: 10px;
}

.assistant-input {
  flex: 1;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 6px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
}

.assistant-input::placeholder {
  color: #5a7a9a;
}

.send-btn {
  padding: 8px 10px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  border-radius: 6px;
  color: #031020;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover {
  opacity: 0.9;
}

.assistant-result {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: rgba(47, 156, 255, 0.06);
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 6px;
}

.result-title {
  font-size: 11px;
  color: #8fa9c8;
  margin-bottom: 6px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
}

.result-item:hover {
  background: rgba(47, 156, 255, 0.08);
}

.result-name {
  font-size: 12px;
  color: #e8f3ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-status {
  font-size: 11px;
  flex-shrink: 0;
  margin-left: 8px;
}

.quick-questions {
  margin-top: 8px;
}

.quick-title {
  font-size: 11px;
  color: #5a7a9a;
  margin-bottom: 6px;
}

.quick-question-btn {
  display: block;
  width: 100%;
  padding: 7px 10px;
  background: rgba(105, 227, 111, 0.04);
  border: none;
  border-radius: 5px;
  color: #8fa9c8;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  margin-bottom: 5px;
  transition: all 0.2s;
  line-height: 1.4;
  white-space: normal;
  min-height: 32px;
}

.quick-question-btn:hover {
  background: rgba(105, 227, 111, 0.08);
  color: #e8f3ff;
}

.focus-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.focus-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  border-left: 2px solid transparent;
}

.focus-item:hover {
  background: rgba(105, 227, 111, 0.06);
}

.focus-item.overdue {
  border-left-color: #ff4f5e;
}

.focus-item.urgent {
  border-left-color: #ffb347;
}

.focus-item.today {
  border-left-color: #2f9cff;
}

.focus-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.focus-name {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.focus-status {
  font-size: 11px;
  color: #8fa9c8;
  flex-shrink: 0;
}

.focus-value {
  font-size: 11px;
  font-weight: 500;
}

.focus-item.overdue .focus-value {
  color: #ff4f5e;
}

.focus-item.urgent .focus-value {
  color: #ffb347;
}

.focus-item.today .focus-value {
  color: #2f9cff;
}

.focus-item.normal .focus-value {
  color: #69e36f;
}
</style>
