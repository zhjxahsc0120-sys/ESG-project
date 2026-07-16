<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Upload, FolderOpen, Send, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import {
  workspaceStatusCards as mockWorkspaceStatusCards,
  allUploadTasks,
  todayFocusList,
  quickQuestions,
} from '@/data/workspace.mock'
import { getWorkspaceSummary, getWorkspaceTasks } from '@/services/api'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { onWorkspaceRefresh } from '@/utils/workspaceRefresh'

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

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.scopes.some(scope => ['summary', 'tasks'].includes(scope))) {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const [summaryRes, tasksRes] = await Promise.all([
    getWorkspaceSummary(),
    getWorkspaceTasks(),
  ])
  
  if (summaryRes) {
    statusCards.value = [
      { label: '当前待办', value: summaryRes.currentTodo, unit: '项', color: '#8fa9c8' },
      { label: '待上传', value: summaryRes.pendingUpload, unit: '项', color: '#2f9cff' },
      { label: '待补正', value: summaryRes.pendingCorrection, unit: '项', color: '#ffb347' },
      { label: '待提交', value: summaryRes.pendingSubmit, unit: '项', color: '#a66cff' },
      { label: '审核中', value: summaryRes.underReview, unit: '项', color: '#a66cff' },
      { label: '已完成', value: summaryRes.completed, unit: '项', color: '#69e36f' },
    ]
  }
  
  if (tasksRes && tasksRes.items && tasksRes.items.length > 0) {
    taskList.value = tasksRes.items.map(item => ({
      ...item,
      daysOverdue: undefined,
      priorityCode: item.priorityCode || 'NORMAL',
    })) as UploadTask[]
  }
}

function handleStatusCardClick(label: string) {
  let status = ''
  if (label === '待上传') status = '待上传'
  else if (label === '待补正') status = '待补正'
  else if (label === '待提交') status = '待提交'
  emit('navigate', 'tasks', status)
}

function handleUploadClick() {
  emit('navigate', 'smart-upload')
}

function handleBatchImport() {
  emit('navigate', 'smart-upload')
}

function handleTaskClick(taskId: string) {
  emit('openTask', taskId)
}

function handleQuickQuestion(question: string) {
  inputValue.value = question
  assistantMessage.value = ''
}

function handleSend() {
  if (!inputValue.value.trim()) return
  assistantMessage.value = `已收到问题「${inputValue.value}」。智能助手能力为原型预留，暂未接入真实 AI 问答服务。`
  inputValue.value = ''
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
    case '待上传': return '#2f9cff'
    case '待补正': return '#ffb347'
    case '待提交': return '#a66cff'
    case '审核退回': return '#ff4f5e'
    default: return '#8fa9c8'
  }
}

const statusPriority: Record<string, number> = {
  '已逾期': 0,
  '审核退回': 1,
  '即将到期': 2,
  '待补正': 3,
  '待上传': 4,
  '待提交': 5,
}

const sortedTasks = computed(() => {
  return [...taskList.value].sort((a, b) => {
    const aType = a.daysOverdue ? '已逾期' : a.status
    const bType = b.daysOverdue ? '已逾期' : b.status
    const aPriority = statusPriority[aType] ?? 9
    const bPriority = statusPriority[bType] ?? 9
    if (aPriority !== bPriority) return aPriority - bPriority
    return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
  })
})

const totalPages = computed(() => Math.ceil(sortedTasks.value.length / pageSize))

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedTasks.value.slice(start, start + pageSize)
})

watch(sortedTasks, () => {
  currentPage.value = 1
})

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function getPageNumbers() {
  const pages: number[] = []
  for (let i = 1; i <= totalPages.value; i++) pages.push(i)
  return pages
}

function getFocusTypeClass(type: string) {
  switch (type) {
    case 'overdue': return 'overdue'
    case 'urgent': return 'urgent'
    case 'today': return 'today'
    default: return 'normal'
  }
}
</script>

<template>
  <div class="workspace-home">
    <div class="main-content">
      <div class="status-cards">
        <div
          v-for="card in statusCards"
          :key="card.label"
          class="status-card"
          :style="{ '--accent-color': card.color }"
          @click="handleStatusCardClick(card.label)"
        >
          <div class="card-label">{{ card.label }}</div>
          <div class="card-value">{{ card.value }}</div>
          <div class="card-unit">{{ card.unit }}</div>
          <div v-if="card.subText" class="card-subtext">{{ card.subText }}</div>
        </div>
      </div>

      <div class="smart-upload-section">
        <div class="section-header">
          <div class="section-title">ESG 智能入库</div>
          <div class="section-subtitle">上传新资料，智能解析并匹配待办任务</div>
        </div>
        <div class="upload-buttons">
          <button class="upload-btn primary" @click="handleUploadClick">
            <Upload :size="18" />
            <span>上传文件</span>
          </button>
          <button class="upload-btn" @click="handleBatchImport">
            <FolderOpen :size="18" />
            <span>批量导入</span>
          </button>
        </div>
      </div>

      <div class="tasks-section">
        <div class="section-header">
          <div class="section-title">我的上传任务</div>
        </div>
        <div class="tasks-table-wrapper">
          <table class="tasks-table">
            <thead>
              <tr>
                <th>任务名称</th>
                <th>ESG模块</th>
                <th>截止时间</th>
                <th>资料进度</th>
                <th>状态</th>
                <th>下一步</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in paginatedTasks"
                :key="task.id"
                class="task-row"
                @click="handleTaskClick(task.id)"
              >
                <td class="task-name">{{ task.name }}</td>
                <td>
                  <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                    {{ task.module }} {{ task.moduleName }}
                  </span>
                </td>
                <td :class="{ 'overdue': task.daysOverdue }">{{ task.deadlineDisplay }}</td>
                <td>
                  <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: `${(task.progressCurrent / task.progressTotal) * 100}%` }"></div>
                  </div>
                  <span class="progress-text">{{ task.progressCurrent }}/{{ task.progressTotal }}</span>
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
        <div class="pagination">
          <div class="pagination-info">共 {{ sortedTasks.length }} 项，每页 {{ pageSize }} 项</div>
          <div class="pagination-controls">
            <button class="page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
              <ChevronLeft :size="16" />
            </button>
            <button
              v-for="p in getPageNumbers()"
              :key="p"
              class="page-btn"
              :class="{ active: currentPage === p }"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
            <button class="page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
              <ChevronRight :size="16" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <aside class="right-sidebar">
      <div class="assistant-card">
        <div class="card-header">
          <div class="card-title">ESG 智能助手</div>
        </div>
        <div class="greeting">Hi，项目管理员</div>
        <div class="input-wrapper">
          <input
            v-model="inputValue"
            type="text"
            placeholder="询问待办任务、缺失资料或上传要求"
            class="assistant-input"
            @keyup.enter="handleSend"
          />
          <button class="send-btn" @click="handleSend">
            <Send :size="16" />
          </button>
        </div>
        <div v-if="assistantMessage" class="assistant-message">
          {{ assistantMessage }}
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
          <div class="card-count">最多 4 条</div>
        </div>
        <div class="focus-list">
          <div
            v-for="item in todayFocusList"
            :key="item.id"
            class="focus-item"
            :class="getFocusTypeClass(item.type)"
            @click="handleTaskClick(item.id.replace('f', 't'))"
          >
            <span class="focus-name">{{ item.name }}</span>
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
  grid-template-columns: minmax(0, 1fr) clamp(450px, 28vw, 520px);
  gap: 20px;
  padding: 20px;
  height: calc(100% - 120px);
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 360px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.status-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 12px 18px;
  min-height: 92px;
  cursor: pointer;
  transition: all 0.2s;
}

.status-card:hover {
  border-color: var(--accent-color);
  box-shadow: 0 0 16px rgba(105, 227, 111, 0.1);
}

.card-label {
  font-size: 13px;
  color: #8fa9c8;
  line-height: 20px;
}

.card-value {
  font-size: 30px;
  font-weight: 700;
  color: var(--accent-color);
  line-height: 34px;
  margin-top: 5px;
}

.card-unit {
  font-size: 12px;
  color: #8fa9c8;
  margin-left: 4px;
}

.card-subtext {
  font-size: 11px;
  color: #5a7a9a;
  line-height: 18px;
  margin-top: 2px;
}

.smart-upload-section {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px 20px;
}

.section-header {
  margin-bottom: 12px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #e8f3ff;
}

.section-subtitle {
  font-size: 11px;
  color: #8fa9c8;
  margin-top: 3px;
}

.upload-buttons {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
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

.upload-btn.primary:hover {
  opacity: 0.9;
}

.tasks-section {
  flex: 1;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.tasks-table-wrapper {
  flex: 1;
  overflow-x: auto;
  min-height: 0;
}

.tasks-table {
  width: 100%;
  border-collapse: collapse;
}

.tasks-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);
  height: 44px;
}

.task-row {
  cursor: pointer;
  transition: background 0.2s;
  height: 58px;
  min-height: 58px;
}

.task-row:hover {
  background: rgba(105, 227, 111, 0.05);
}

.task-row td {
  padding: 10px 12px;
  font-size: 13px;
  color: #e8f3ff;
  border-bottom: 1px solid rgba(105, 227, 111, 0.05);
}

.task-name {
  font-weight: 500;
}

.module-tag, .status-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.progress-bar {
  width: 80px;
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
  margin-left: 10px;
  font-size: 12px;
  color: #8fa9c8;
}

.next-step-btn {
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 4px;
  color: #69e36f;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.next-step-btn:hover {
  background: rgba(105, 227, 111, 0.2);
}

.overdue {
  color: #ff4f5e;
}

.pagination {
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-top: 1px solid rgba(74, 144, 196, 0.2);
  margin-top: 8px;
  flex-shrink: 0;
}

.pagination-info {
  font-size: 12px;
  color: #5a7a9a;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-btn {
  min-width: 28px;
  height: 28px;
  padding: 0 8px;
  background: rgba(105, 227, 111, 0.05);
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: rgba(105, 227, 111, 0.15);
  color: #e8f3ff;
}

.page-btn.active {
  background: rgba(47, 156, 255, 0.2);
  border-color: rgba(47, 156, 255, 0.5);
  color: #2f9cff;
  font-weight: 600;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.assistant-card, .focus-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.card-count {
  font-size: 11px;
  color: #5a7a9a;
}

.greeting {
  font-size: 13px;
  color: #8fa9c8;
  margin-bottom: 12px;
}

.input-wrapper {
  display: flex;
  gap: 8px;
}

.assistant-input {
  flex: 1;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
}

.assistant-input::placeholder {
  color: #5a7a9a;
}

.send-btn {
  padding: 10px;
  background: rgba(105, 227, 111, 0.15);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 6px;
  color: #69e36f;
  cursor: pointer;
}

.send-btn:hover {
  background: rgba(105, 227, 111, 0.25);
}

.assistant-message {
  margin-top: 10px;
  padding: 9px 10px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.18);
  border-radius: 6px;
  color: #9fc7ff;
  font-size: 12px;
  line-height: 1.5;
}

.quick-questions {
  margin-top: 14px;
}

.quick-title {
  font-size: 11px;
  color: #5a7a9a;
  margin-bottom: 8px;
}

.quick-question-btn {
  display: block;
  width: 100%;
  padding: 9px 12px;
  background: rgba(105, 227, 111, 0.05);
  border: none;
  border-radius: 5px;
  color: #8fa9c8;
  font-size: 12px;
  text-align: left;
  cursor: pointer;
  margin-bottom: 6px;
  transition: all 0.2s;
  line-height: 1.4;
  white-space: normal;
  min-height: 38px;
}

.quick-question-btn:hover {
  background: rgba(105, 227, 111, 0.1);
  color: #e8f3ff;
}

.focus-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.focus-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.focus-item:hover {
  background: rgba(105, 227, 111, 0.08);
}

.focus-name {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.4;
  white-space: normal;
}

.focus-value {
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
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
