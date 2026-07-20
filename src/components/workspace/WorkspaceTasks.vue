<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Link2, Download, Sparkles } from 'lucide-vue-next'
import { allUploadTasks } from '@/data/workspace.mock'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { TASK_STATUS_COLORS, MODULE_COLORS } from '@/types/workspace'

const props = defineProps<{
  initialStatus?: string
}>()

const emit = defineEmits<{
  (e: 'openTask', taskId: string): void
}>()

const searchKeyword = ref('')
const selectedStatus = ref('当前待办')
const selectedIds = ref<string[]>([])
const taskList = ref<UploadTask[]>([...allUploadTasks])

const statusCards = computed<StatusCard[]>(() => {
  const list = taskList.value
  const todoStatuses = ['待上传', '待补正', '待提交', '审核中']
  const todo = list.filter(t => todoStatuses.includes(t.status)).length
  const overdue = list.filter(t => t.isOverdue).length
  const upcoming = list.filter(t => !t.isOverdue).length
  const pending = list.filter(t => t.status === '待上传').length
  const correcting = list.filter(t => t.status === '待补正').length
  const ready = list.filter(t => t.status === '待提交').length
  const reviewing = list.filter(t => t.status === '审核中').length
  const done = list.filter(t => t.status === '已完成' || t.status === '已归档').length
  return [
    { label: '当前待办', value: todo, unit: '项', subText: `已逾期 ${overdue} 项`, subText2: `3日内到期 ${upcoming} 项`, color: '#8fa9c8' },
    { label: '待上传', value: pending, unit: '项', color: '#2f9cff' },
    { label: '待补正', value: correcting, unit: '项', color: '#ffb347' },
    { label: '待提交', value: ready, unit: '项', color: '#a66cff' },
    { label: '审核中', value: reviewing, unit: '项', color: '#a66cff' },
    { label: '已完成', value: done, unit: '项', color: '#69e36f' },
  ]
})

const hasSearch = ref(false)
const searchResultHint = ref('')

const filterModule = ref('')
const filterCycle = ref('')
const filterSource = ref('')
const filterDeadlineStart = ref('')
const filterDeadlineEnd = ref('')
const filterAssignee = ref('')

const currentPage = ref(1)
const pageSize = ref(10)
const showAdvancedFilter = ref(false)

const searchExamples = [
  '显示本周到期的水保资料',
  '查找所有待补正的高风险作业资料',
  '显示7月月报尚未完成的任务',
]

watch(() => props.initialStatus, (newStatus) => {
  if (newStatus) {
    if (newStatus === 'todo') {
      selectedStatus.value = '当前待办'
    } else {
      selectedStatus.value = newStatus
    }
  }
}, { immediate: true })

const filteredTasks = computed(() => {
  let results = [...taskList.value]

  if (selectedStatus.value === '当前待办') {
    results = results.filter(t => ['待上传', '待补正', '待提交', '审核中'].includes(t.status))
  } else if (selectedStatus.value !== '全部') {
    results = results.filter(t => t.status === selectedStatus.value)
  }

  if (filterModule.value) {
    results = results.filter(t => t.module === filterModule.value)
  }

  if (filterSource.value) {
    results = results.filter(t => t.sourceType === filterSource.value)
  }

  if (filterCycle.value) {
    results = results.filter(t => t.cycle?.includes(filterCycle.value))
  }

  if (filterAssignee.value) {
    results = results.filter(t => t.assignee?.includes(filterAssignee.value))
  }

  if (searchKeyword.value.trim()) {
    const query = searchKeyword.value.toLowerCase()
    results = results.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.sourceKpiName?.toLowerCase().includes(query) ||
      t.relatedReport?.toLowerCase().includes(query)
    )
  }

  return results
})

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTasks.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTasks.value.length / pageSize.value)))

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

watch(filteredTasks, () => {
  currentPage.value = 1
})

const selectedCount = computed(() => selectedIds.value.length)

const canBatchSubmit = computed(() => {
  if (selectedIds.value.length === 0) return false
  const tasks = selectedIds.value.map(id => taskList.value.find(t => t.id === id)).filter(Boolean) as UploadTask[]
  const statuses = new Set(tasks.map(t => t.status))
  if (statuses.size > 1) return false
  if (!statuses.has('待提交')) return false
  return tasks.every(t => t.progressCurrent === t.progressTotal)
})

const batchSubmitDisabledReason = computed(() => {
  if (selectedIds.value.length === 0) return '请先选择任务'
  const tasks = selectedIds.value.map(id => taskList.value.find(t => t.id === id)).filter(Boolean) as UploadTask[]
  const statuses = new Set(tasks.map(t => t.status))
  if (statuses.size > 1) return '不同状态任务不能混合提交'
  if (!statuses.has('待提交')) return '仅待提交状态的任务可批量提交'
  const incomplete = tasks.filter(t => t.progressCurrent !== t.progressTotal)
  if (incomplete.length > 0) return `所选任务存在资料缺失，暂不可提交（${incomplete.length} 项未满足）`
  return ''
})

function handleStatusCardClick(status: string) {
  selectedStatus.value = status
  hasSearch.value = false
  searchKeyword.value = ''
  currentPage.value = 1
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
  if (selectedIds.value.length === paginatedTasks.value.length) {
    selectedIds.value = selectedIds.value.filter(id => !paginatedTasks.value.find(t => t.id === id))
  } else {
    const pageIds = paginatedTasks.value.map(t => t.id)
    for (const id of pageIds) {
      if (!selectedIds.value.includes(id)) {
        selectedIds.value.push(id)
      }
    }
  }
}

function handleSearch() {
  hasSearch.value = true
  currentPage.value = 1
}

function handleReset() {
  searchKeyword.value = ''
  filterModule.value = ''
  filterCycle.value = ''
  filterSource.value = ''
  filterDeadlineStart.value = ''
  filterDeadlineEnd.value = ''
  filterAssignee.value = ''
  selectedStatus.value = '当前待办'
  hasSearch.value = false
  searchResultHint.value = ''
  currentPage.value = 1
}

function handleExampleClick(example: string) {
  searchKeyword.value = example
  handleSearch()
}

function handleBatchLink() {
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务。批量关联资料功能已触发。`
}

function handleBatchSubmit() {
  if (!canBatchSubmit.value) {
    searchResultHint.value = batchSubmitDisabledReason.value
    return
  }
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务，提交成功。`
}

function handleBatchExport() {
  searchResultHint.value = `已导出 ${selectedCount.value} 项任务的资料清单。`
}

function handleClearSelection() {
  selectedIds.value = []
}

function getModuleColor(module: string) {
  return MODULE_COLORS[module] || '#8fa9c8'
}

function getStatusColor(status: string) {
  return TASK_STATUS_COLORS[status] || '#8fa9c8'
}

function isSelected(taskId: string) {
  return selectedIds.value.includes(taskId)
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

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function changePageSize(size: number) {
  pageSize.value = size
  currentPage.value = 1
}

function isAllSelectedOnPage() {
  return paginatedTasks.value.length > 0 && paginatedTasks.value.every(t => selectedIds.value.includes(t.id))
}
</script>

<template>
  <div class="workspace-tasks">
    <div class="ws-page-header">
      <div class="ws-page-title-group">
        <div class="ws-page-title">我的上传任务</div>
        <div class="ws-page-subtitle">查询并办理本人负责的资料任务</div>
      </div>
    </div>

    <div class="ws-status-cards cols-6">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="ws-status-card"
        :class="{ active: selectedStatus === card.label }"
        :style="{ '--accent-color': card.color }"
        @click="handleStatusCardClick(card.label)"
      >
        <div class="ws-card-label">{{ card.label }}</div>
        <div class="ws-card-value-row">
          <span class="ws-card-value">{{ card.value }}</span>
          <span class="ws-card-unit">{{ card.unit }}</span>
        </div>
      </div>
    </div>

    <div class="filter-section">
      <div class="search-row">
        <div class="ai-search-box">
          <Sparkles :size="16" class="search-icon" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="可输入任务名称、缺失资料、截止时间或关联指标"
            @keyup.enter="handleSearch"
          />
          <button class="search-btn" @click="handleSearch">搜索</button>
        </div>
        <button class="advanced-toggle" @click="showAdvancedFilter = !showAdvancedFilter">
          {{ showAdvancedFilter ? '收起筛选' : '高级筛选' }}
        </button>
      </div>

      <div v-if="showAdvancedFilter" class="filter-controls">
        <select v-model="filterModule" class="filter-select">
          <option value="">ESG模块</option>
          <option value="E">E-环境环保</option>
          <option value="S">S-社会责任</option>
          <option value="G">G-治理合规</option>
        </select>
        <input v-model="filterCycle" type="text" class="filter-input" placeholder="资料周期" />
        <select v-model="filterSource" class="filter-select">
          <option value="">任务来源</option>
          <option value="KPI指标">KPI指标</option>
          <option value="月报任务">月报任务</option>
          <option value="业务事项">业务事项</option>
          <option value="周期任务">周期任务</option>
          <option value="审核补正">审核补正</option>
          <option value="临时任务">临时任务</option>
        </select>
        <input v-model="filterDeadlineStart" type="date" class="filter-input" />
        <input v-model="filterDeadlineEnd" type="date" class="filter-input" />
        <input v-model="filterAssignee" type="text" class="filter-input" placeholder="经办人" />
        <button class="filter-btn primary" @click="handleSearch">筛选</button>
        <button class="filter-btn" @click="handleReset">重置</button>
      </div>

      <div v-if="!hasSearch && !showAdvancedFilter" class="search-examples">
        <span class="example-label">搜索示例：</span>
        <span class="example-item" v-for="(ex, idx) in searchExamples" :key="idx" @click="handleExampleClick(ex)">{{ ex }}</span>
      </div>

      <div v-if="searchResultHint" class="search-result-hint">{{ searchResultHint }}</div>
    </div>

    <div v-if="selectedCount > 0" class="batch-section">
      <div class="batch-info">
        <label class="select-all">
          <input type="checkbox" :checked="isAllSelectedOnPage()" @change="toggleSelectAll" />
          已选择 {{ selectedCount }} 项
        </label>
        <button class="clear-btn" @click="handleClearSelection">清空选择</button>
      </div>
      <div class="batch-actions">
        <button class="batch-btn" @click="handleBatchLink">
          <Link2 :size="14" />
          <span>批量关联已有资料</span>
        </button>
        <button class="batch-btn primary" :class="{ disabled: !canBatchSubmit }" :disabled="!canBatchSubmit" @click="handleBatchSubmit">
          批量提交
        </button>
        <button class="batch-btn" @click="handleBatchExport">
          <Download :size="14" />
          <span>批量导出资料清单</span>
        </button>
      </div>
    </div>

    <div class="ws-table-container">
      <div class="ws-table-header-wrapper">
        <table class="ws-table">
          <colgroup>
            <col class="col-checkbox" />
            <col class="col-name" />
            <col class="col-source" />
            <col class="col-module" />
            <col class="col-cycle" />
            <col class="col-deadline" />
            <col class="col-progress" />
            <col class="col-status" />
            <col class="col-action" />
          </colgroup>
          <thead>
            <tr>
              <th class="col-checkbox">
                <input type="checkbox" :checked="isAllSelectedOnPage()" @change="toggleSelectAll" />
              </th>
              <th>任务名称</th>
              <th>来源/关联对象</th>
              <th>ESG模块</th>
              <th>资料周期</th>
              <th>截止时间</th>
              <th>资料进度</th>
              <th>状态</th>
              <th>下一步</th>
            </tr>
          </thead>
        </table>
      </div>
      <div class="ws-table-body-wrapper">
        <table class="ws-table">
          <colgroup>
            <col class="col-checkbox" />
            <col class="col-name" />
            <col class="col-source" />
            <col class="col-module" />
            <col class="col-cycle" />
            <col class="col-deadline" />
            <col class="col-progress" />
            <col class="col-status" />
            <col class="col-action" />
          </colgroup>
          <tbody>
            <tr
              v-for="task in paginatedTasks"
              :key="task.id"
              :class="{ selected: isSelected(task.id) }"
              @click="emit('openTask', task.id)"
            >
              <td class="col-checkbox">
                <input type="checkbox" :checked="isSelected(task.id)" @click.stop="toggleSelect(task.id)" />
              </td>
              <td class="task-name">{{ task.name }}</td>
              <td class="task-source">{{ getSourceDisplay(task) }}</td>
              <td>
                <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                  {{ task.module }} {{ task.moduleName }}
                </span>
              </td>
              <td>{{ task.cycle }}</td>
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
                <button class="next-step-btn" @click.stop="emit('openTask', task.id)">
                  {{ task.nextStep }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="ws-pagination-bar">
        <div class="ws-pagination-info">
          共 <span class="highlight">{{ filteredTasks.length }}</span> 条记录，第 {{ currentPage }}/{{ totalPages }} 页
        </div>
        <div class="ws-pagination-controls">
          <select v-model.number="pageSize" class="ws-page-size-select" @change="changePageSize(pageSize)">
            <option :value="10">10 条/页</option>
            <option :value="20">20 条/页</option>
            <option :value="30">30 条/页</option>
          </select>
          <button class="ws-page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">上一页</button>
          <button
            v-for="p in getPageNumbers()"
            :key="p"
            class="ws-page-btn"
            :class="{ active: currentPage === p }"
            @click="goToPage(p)"
          >
            {{ p }}
          </button>
          <button class="ws-page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">下一页</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-tasks {
  padding: 14px 16px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.filter-section {
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.08);
  border-radius: 8px;
  padding: 12px;
  flex-shrink: 0;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 6px;
  padding: 7px 10px;
}

.search-icon {
  color: #69e36f;
  flex-shrink: 0;
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
  padding: 5px 12px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  border-radius: 4px;
  color: #031020;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.advanced-toggle {
  padding: 6px 12px;
  background: rgba(105, 227, 111, 0.06);
  border: 1px solid rgba(105, 227, 111, 0.18);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.advanced-toggle:hover {
  color: #69e36f;
  border-color: rgba(105, 227, 111, 0.3);
}

.filter-controls {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-select,
.filter-input {
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.25);
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

.filter-btn {
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.06);
  border: 1px solid rgba(105, 227, 111, 0.18);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:hover {
  color: #e8f3ff;
}

.filter-btn.primary {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  color: #031020;
  font-weight: 600;
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
  padding: 3px 8px;
  background: rgba(105, 227, 111, 0.04);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.example-item:hover {
  color: #69e36f;
  background: rgba(105, 227, 111, 0.08);
}

.search-result-hint {
  font-size: 11px;
  color: #69e36f;
  margin-top: 8px;
}

.batch-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.2);
  border-radius: 6px;
  flex-shrink: 0;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 10px;
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
  border: 1px solid rgba(255, 79, 94, 0.25);
  border-radius: 4px;
  color: #ff4f5e;
  font-size: 11px;
  cursor: pointer;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.batch-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.25);
  border-radius: 4px;
  color: #69e36f;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.batch-btn:hover {
  background: rgba(105, 227, 111, 0.15);
}

.batch-btn.primary {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  color: #031020;
  font-weight: 600;
}

.batch-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ws-table {
  table-layout: fixed;
}

.col-checkbox {
  width: 40px;
}

.col-name {
  width: 20%;
}

.col-source {
  width: 22%;
}

.col-module {
  width: 10%;
}

.col-cycle {
  width: 12%;
}

.col-deadline {
  width: 12%;
}

.col-progress {
  width: 10%;
}

.col-status {
  width: 8%;
}

.col-action {
  width: 10%;
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
  gap: 6px;
}

.progress-bar {
  flex: 1;
  height: 5px;
  background: rgba(105, 227, 111, 0.08);
  border-radius: 3px;
  overflow: hidden;
  min-width: 40px;
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
</style>
