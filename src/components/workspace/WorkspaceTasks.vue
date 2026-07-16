<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Upload, Link2 } from 'lucide-vue-next'
import { allUploadTasks, taskStatusCards as mockTaskStatusCards } from '@/data/workspace.mock'
import { getWorkspaceSummary, getWorkspaceTasks } from '@/services/api'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const props = defineProps<{
  initialStatus?: string
}>()

const emit = defineEmits<{
  (e: 'openTask', taskId: string): void
}>()

const searchKeyword = ref('')
const selectedStatus = ref('当前待办')
const selectedIds = ref<string[]>(['t1', 't6'])
const taskList = ref<UploadTask[]>([...allUploadTasks])
const statusCards = ref<StatusCard[]>([...mockTaskStatusCards])

const hasSearch = ref(false)
const searchResultHint = ref('')

const filterModule = ref('')
const filterCycle = ref('')
const filterCycleType = ref('')
const filterDeadlineStart = ref('')
const filterDeadlineEnd = ref('')
const filterAssignee = ref('')

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  if (props.initialStatus) {
    selectedStatus.value = props.initialStatus
  }
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (!payload.scopes.some(scope => ['summary', 'tasks'].includes(scope))) return
    if (hasSearch.value) {
      handleAiSearch()
    } else {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  await loadDataWithParams({})
}

async function loadDataWithParams(params: {
  module?: string
  status?: string
  keyword?: string
  cycle?: string
  cycleType?: string
  deadlineStart?: string
  deadlineEnd?: string
  assignee?: string
}) {
  const [summaryRes, tasksRes] = await Promise.all([
    getWorkspaceSummary(),
    getWorkspaceTasks(params),
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
  } else {
    taskList.value = [...allUploadTasks]
  }
}

const filteredTasks = computed(() => {
  if (!hasSearch.value) {
    if (selectedStatus.value === '当前待办') {
      return taskList.value.filter(t => ['待上传', '待补正', '待提交', '审核中', '审核退回'].includes(t.status))
    }
    return taskList.value.filter(t => t.status === selectedStatus.value)
  }
  
  const query = searchKeyword.value.toLowerCase()
  let results = taskList.value
  
  if (query.includes('逾期') || query.includes('过期')) {
    results = results.filter(t => t.daysOverdue)
  } else if (query.includes('待上传') || query.includes('需要上传')) {
    results = results.filter(t => t.status === '待上传')
  } else if (query.includes('退回') || query.includes('审核退回')) {
    results = results.filter(t => t.status === '审核退回')
  } else if (query.includes('补正') || query.includes('重新提交')) {
    results = results.filter(t => t.status === '待补正')
  } else if (query.includes('待提交')) {
    results = results.filter(t => t.status === '待提交')
  } else if (query.includes('审核中')) {
    results = results.filter(t => t.status === '审核中')
  } else if (query.includes('已完成')) {
    results = results.filter(t => t.status === '已完成')
  }
  
  if (query.includes('e组') || query.includes('环境')) {
    results = results.filter(t => t.module === 'E')
  } else if (query.includes('s组') || query.includes('社会')) {
    results = results.filter(t => t.module === 'S')
  } else if (query.includes('g组') || query.includes('治理')) {
    results = results.filter(t => t.module === 'G')
  }
  
  if (query.includes('本月') || query.includes('7月')) {
    results = results.filter(t => t.cycle.includes('2026-07') || t.cycle.includes('2026-Q3'))
  } else if (query.includes('本周')) {
    results = results.filter(t => {
      const deadline = new Date(t.deadline)
      const now = new Date()
      const diffDays = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      return diffDays >= 0 && diffDays <= 7
    })
  }
  
  if (!query.match(/(逾期|上传|退回|补正|待提交|审核中|已完成|e组|s组|g组|本月|本周|7月)/)) {
    results = taskList.value.filter(t => 
      t.name.toLowerCase().includes(query) || 
      t.moduleName.toLowerCase().includes(query)
    )
  }
  
  return results
})

const selectedCount = computed(() => selectedIds.value.length)

const canBatchSubmit = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.every(id => {
    const task = taskList.value.find(t => t.id === id)
    return task?.progressCurrent === task?.progressTotal
  })
})

const batchSubmitDisabledReason = computed(() => {
  if (selectedIds.value.length === 0) return '请先选择任务'
  const incomplete = selectedIds.value.filter(id => {
    const task = taskList.value.find(t => t.id === id)
    return task?.progressCurrent !== task?.progressTotal
  })
  if (incomplete.length > 0) return `所选任务存在资料缺失或格式异常，暂不可提交（${incomplete.length} 项未满足）`
  return ''
})

function handleStatusCardClick(status: string) {
  selectedStatus.value = status
  hasSearch.value = false
  searchKeyword.value = ''
}

function toggleSelect(taskId: string) {
  const index = selectedIds.value.indexOf(taskId)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(taskId)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.length === filteredTasks.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredTasks.value.map(t => t.id)
  }
}

function handleAiSearch() {
  hasSearch.value = true
  searchResultHint.value = ''

  const params: {
    module?: string
    status?: string
    keyword?: string
    cycle?: string
    cycleType?: string
    deadlineStart?: string
    deadlineEnd?: string
    assignee?: string
  } = {}

  if (filterModule.value) params.module = filterModule.value
  if (filterCycle.value) params.cycle = filterCycle.value
  if (filterCycleType.value) params.cycleType = filterCycleType.value
  if (filterDeadlineStart.value) params.deadlineStart = filterDeadlineStart.value
  if (filterDeadlineEnd.value) params.deadlineEnd = filterDeadlineEnd.value
  if (filterAssignee.value) params.assignee = filterAssignee.value

  if (searchKeyword.value.trim()) {
    params.keyword = searchKeyword.value.trim()
  }

  if (selectedStatus.value !== '当前待办') {
    params.status = selectedStatus.value
  }

  loadDataWithParams(params)
}

function handleClearSearch() {
  hasSearch.value = false
  searchKeyword.value = ''
  searchResultHint.value = ''
  selectedStatus.value = '当前待办'
  filterModule.value = ''
  filterCycle.value = ''
  filterCycleType.value = ''
  filterDeadlineStart.value = ''
  filterDeadlineEnd.value = ''
  filterAssignee.value = ''
  loadData()
}

function handleBatchLink() {
  hasSearch.value = true
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务。批量关联资料为原型预留功能，暂未接入批量办理流程。`
}

function handleBatchSubmit() {
  if (!canBatchSubmit.value) {
    hasSearch.value = true
    searchResultHint.value = batchSubmitDisabledReason.value
    return
  }
  hasSearch.value = true
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务。批量提交为原型预留功能，暂未接入批量审核流程。`
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
    case '审核中': return '#a66cff'
    case '审核退回': return '#ff4f5e'
    case '已完成': return '#69e36f'
    default: return '#8fa9c8'
  }
}

function isSelected(taskId: string) {
  return selectedIds.value.includes(taskId)
}
</script>

<template>
  <div class="workspace-tasks">
    <div class="page-header">
      <div class="page-title">我的上传任务</div>
    </div>

    <div class="status-cards">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="status-card"
        :class="{ active: selectedStatus === card.label }"
        :style="{ '--accent-color': card.color }"
        @click="handleStatusCardClick(card.label)"
      >
        <div class="card-icon">
          <Upload v-if="card.label === '待上传'" :size="20" />
          <Filter v-else-if="card.label === '待补正'" :size="20" />
          <Link2 v-else-if="card.label === '待提交'" :size="20" />
          <Calendar v-else-if="card.label === '审核中'" :size="20" />
        </div>
        <div class="card-label">{{ card.label }}</div>
        <div class="card-value">{{ card.value }}</div>
        <div class="card-unit">{{ card.unit }}</div>
      </div>
    </div>

    <div class="filter-section">
      <div class="ai-search-header">
        <span class="ai-search-title">ESG智能助手</span>
        <button v-if="hasSearch" class="clear-search-btn" @click="handleClearSearch">清除搜索</button>
      </div>
      <div class="ai-search-box">
        <Search :size="16" />
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="询问待办任务、缺失资料、截止时间或任务状态" 
          @keyup.enter="handleAiSearch"
        />
        <button class="search-btn" @click="handleAiSearch">搜索</button>
      </div>
      <div class="filter-controls">
        <select v-model="filterModule" class="filter-select" @change="handleAiSearch">
          <option value="">全部模块</option>
          <option value="E">E-环境环保</option>
          <option value="S">S-社会责任</option>
          <option value="G">G-公司治理</option>
        </select>
        <input v-model="filterCycle" type="text" class="filter-input" placeholder="资料周期" @keyup.enter="handleAiSearch" />
        <select v-model="filterCycleType" class="filter-select" @change="handleAiSearch">
          <option value="">周期类型</option>
          <option value="MONTHLY">月度</option>
          <option value="QUARTERLY">季度</option>
          <option value="ANNUAL">年度</option>
        </select>
        <input v-model="filterDeadlineStart" type="date" class="filter-input" @change="handleAiSearch" />
        <input v-model="filterDeadlineEnd" type="date" class="filter-input" @change="handleAiSearch" />
        <input v-model="filterAssignee" type="text" class="filter-input" placeholder="经办人" @keyup.enter="handleAiSearch" />
      </div>
      <div v-if="hasSearch" class="search-result-hint">{{ searchResultHint }}</div>
      <div v-if="!hasSearch" class="search-examples">
        <span class="example-label">输入示例：</span>
        <span class="example-item">哪些任务已经逾期？</span>
        <span class="example-item">本周需要上传哪些资料？</span>
        <span class="example-item">有哪些任务被审核退回？</span>
        <span class="example-item">哪些任务还需要补正？</span>
        <span class="example-item">显示E组本月待上传任务</span>
      </div>
    </div>

    <div class="batch-section">
      <div class="batch-info">
        <label class="select-all">
          <input type="checkbox" :checked="selectedCount === filteredTasks.length && filteredTasks.length > 0" @change="toggleSelectAll" />
          已选择 {{ selectedCount }} 项
        </label>
        <button class="clear-btn" v-if="selectedCount > 0" @click="selectedIds = []">清空</button>
      </div>
      <div class="batch-actions">
        <button class="batch-btn" @click="handleBatchLink">批量关联资料</button>
        <button class="batch-btn" :class="{ disabled: !canBatchSubmit }" :disabled="!canBatchSubmit">
          批量提交（条件不满足）
        </button>
      </div>
    </div>

    <div class="tasks-table-wrapper">
      <table class="tasks-table">
        <thead>
          <tr>
            <th class="checkbox-col">
              <input type="checkbox" :checked="selectedCount === filteredTasks.length && filteredTasks.length > 0" @change="toggleSelectAll" />
            </th>
            <th>任务名称</th>
            <th>ESG模块</th>
            <th>资料周期</th>
            <th>截止时间</th>
            <th>资料进度</th>
            <th>当前状态</th>
            <th>下一步</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="task in filteredTasks"
            :key="task.id"
            :class="{ selected: isSelected(task.id) }"
            @click="emit('openTask', task.id)"
          >
            <td class="checkbox-col">
              <input type="checkbox" :checked="isSelected(task.id)" @click.stop="toggleSelect(task.id)" />
            </td>
            <td class="task-name">{{ task.name }}</td>
            <td>
              <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                {{ task.module }} {{ task.moduleName }}
              </span>
            </td>
            <td>{{ task.cycle }}</td>
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
              <button class="next-step-btn" @click.stop="emit('openTask', task.id)">
                {{ task.nextStep }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button class="prev-btn">‹</button>
      <span class="current-page">1</span>
      <button class="next-btn">›</button>
      <span class="page-size">10 条/页</span>
      <span class="total-count">共 {{ filteredTasks.length }} 条</span>
    </div>
  </div>
</template>

<style scoped>
.workspace-tasks {
  padding: 20px;
  height: calc(100% - 120px);
  overflow-y: auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8f3ff;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.status-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.status-card:hover {
  border-color: var(--accent-color);
}

.status-card.active {
  border-color: var(--accent-color);
  background: rgba(105, 227, 111, 0.08);
}

.card-icon {
  color: var(--accent-color);
  margin-bottom: 6px;
}

.card-label {
  font-size: 11px;
  color: #8fa9c8;
}

.card-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent-color);
}

.card-unit {
  font-size: 11px;
  color: #8fa9c8;
}

.filter-section {
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.ai-search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ai-search-title {
  font-size: 13px;
  font-weight: 600;
  color: #69e36f;
}

.clear-search-btn {
  padding: 4px 10px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  border-radius: 4px;
  color: #ff4f5e;
  font-size: 11px;
  cursor: pointer;
}

.ai-search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  padding: 8px 12px;
}

.ai-search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
}

.ai-search-box input::placeholder {
  color: #5a7a9a;
}

.search-btn {
  padding: 6px 14px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  border-radius: 4px;
  color: #031020;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;

  &:active {
    transform: scale(0.97);
    transition-duration: 0.08s;
  }
}

.filter-controls {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.filter-select,
.filter-input {
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(143, 169, 200, 0.2);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  min-width: 100px;
}

.filter-select option,
.filter-input::placeholder {
  color: #5a7a9a;
}

.search-result-hint {
  font-size: 11px;
  color: #69e36f;
  margin-top: 8px;
}

.search-examples {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.example-label {
  font-size: 11px;
  color: #5a7a9a;
}

.example-item {
  font-size: 11px;
  color: #8fa9c8;
  padding: 2px 8px;
  background: rgba(105, 227, 111, 0.05);
  border-radius: 4px;
}

.batch-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  margin-bottom: 16px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #e8f3ff;
  cursor: pointer;
}

.clear-btn {
  padding: 4px 10px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  border-radius: 4px;
  color: #ff4f5e;
  font-size: 11px;
  cursor: pointer;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.batch-btn {
  padding: 8px 16px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 4px;
  color: #69e36f;
  font-size: 12px;
  cursor: pointer;
}

.batch-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tasks-table-wrapper {
  overflow-x: auto;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
}

.tasks-table {
  width: 100%;
  border-collapse: collapse;
}

.tasks-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.checkbox-col {
  width: 40px;
}

.task-row {
  cursor: pointer;
  transition: background 0.2s;
}

.task-row:hover {
  background: rgba(105, 227, 111, 0.05);
}

.task-row.selected {
  background: rgba(105, 227, 111, 0.1);
}

.task-row td {
  padding: 14px 16px;
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
}

.overdue {
  color: #ff4f5e;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.prev-btn, .next-btn {
  width: 28px;
  height: 28px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 14px;
  cursor: pointer;
}

.current-page {
  padding: 6px 12px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border-radius: 4px;
  color: #031020;
  font-size: 12px;
  font-weight: 600;
}

.page-size, .total-count {
  font-size: 12px;
  color: #8fa9c8;
}
</style>
