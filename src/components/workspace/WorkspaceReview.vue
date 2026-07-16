<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Clock, CheckCircle, XCircle, AlertTriangle, ArrowRight, Calendar } from 'lucide-vue-next'
import { reviewStatusCards as mockReviewStatusCards, reviewRecords as mockReviewRecords, reviewTimeline, reviewRequirements } from '@/data/workspace.mock'
import { getReviews, getReviewDetail, getReviewTimeline, getReviewRequirements, approveReview, returnReview } from '@/services/api'
import type { StatusCard, ReviewRecord, ReviewTimeline } from '@/types/workspace'
import type { ReviewTimelineApi, ReviewRequirementApi } from '@/services/api'
import { emitWorkspaceRefresh, onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const emit = defineEmits<{
  (e: 'openTask', taskId: string, forceTab?: string): void
}>()

const activeTab = ref('全部')
const searchKeyword = ref('')
const selectedModule = ref('全部')
const startDate = ref('')
const endDate = ref('')
const statusCards = ref<StatusCard[]>([...mockReviewStatusCards])
const reviewRecordList = ref<ReviewRecord[]>([...mockReviewRecords])
const selectedRecordId = ref(mockReviewRecords[0]?.id || '')
const recordTimelines = ref<Record<string, ReviewTimelineApi[]>>({})
const recordRequirements = ref<Record<string, ReviewRequirementApi[]>>({})
const recordDeadlines = ref<Record<string, string>>({})
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.source === 'review-action') return
    if (payload.scopes.some(scope => ['reviews'].includes(scope))) {
      reloadAll()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const data = await getReviews()
  if (data) {
    if (data.statusCards && data.statusCards.length > 0) {
      statusCards.value = data.statusCards as StatusCard[]
    }
    if (data.items && data.items.length > 0) {
      reviewRecordList.value = data.items.map(item => ({
        id: item.id,
        taskId: item.taskId,
        taskName: item.taskName,
        module: item.module,
        moduleName: item.moduleName,
        submitTime: item.submitTime,
        status: item.status,
        reviewer: item.reviewer,
        commentSummary: item.commentSummary,
        nextStep: item.nextStep,
      })) as ReviewRecord[]
    }
  }
}

function showMessage(message: string, type: 'info' | 'success' | 'error' = 'info') {
  pageMessage.value = message
  pageMessageType.value = type
}

const filteredRecords = computed(() => {
  return reviewRecordList.value.filter(record => {
    if (activeTab.value !== '全部' && record.status !== activeTab.value) return false
    if (searchKeyword.value && !record.taskName.includes(searchKeyword.value)) return false
    if (selectedModule.value !== '全部' && record.module !== selectedModule.value) return false
    return true
  })
})

const selectedRecord = computed(() => {
  return reviewRecordList.value.find(r => r.id === selectedRecordId.value) || reviewRecordList.value[0]
})

const tabs = ['全部', '待审核', '已通过', '已退回', '已归档']

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
    case '待审核': return '#2f9cff'
    case '已通过': return '#69e36f'
    case '已退回': return '#ff4f5e'
    case '补正逾期': return '#ffb347'
    default: return '#8fa9c8'
  }
}

function getTimelineIcon(action: string) {
  if (action.includes('提交')) return ArrowRight
  if (action.includes('校验')) return CheckCircle
  if (action.includes('退回')) return XCircle
  return Clock
}

function handleReset() {
  searchKeyword.value = ''
  selectedModule.value = '全部'
  startDate.value = ''
  endDate.value = ''
}

async function loadReviewDetail(reviewId: string) {
  const [detailRes, timelineRes, requirementsRes] = await Promise.all([
    getReviewDetail(reviewId),
    getReviewTimeline(reviewId),
    getReviewRequirements(reviewId),
  ])

  if (timelineRes && timelineRes.items) {
    recordTimelines.value[reviewId] = timelineRes.items
  }

  if (requirementsRes && requirementsRes.items) {
    recordRequirements.value[reviewId] = requirementsRes.items
  }

  const deadline = detailRes?.rectifyDeadline || detailRes?.correctionDeadline
  if (deadline) {
    recordDeadlines.value[reviewId] = deadline
  }
}

function getTimelineForRecord(recordId: string): ReviewTimeline[] {
  const apiTimeline = recordTimelines.value[recordId]
  if (apiTimeline && apiTimeline.length > 0) {
    return apiTimeline.map(item => ({
      time: item.operatedAt,
      action: item.action,
    }))
  }
  const mockTimelines: Record<string, ReviewTimeline[]> = {
    r1: [
      { time: '2026-08-05 18:00', action: '提交上传（张建国 提交任务）' },
      { time: '2026-08-05 18:05', action: '完整性校验（系统校验通过，共5/7项资料完整）' },
      { time: '2026-08-07 09:15', action: '审核退回（审核人：李安全）' },
    ],
    r2: [
      { time: '2026-08-04 14:00', action: '提交上传（王佳 提交任务）' },
      { time: '2026-08-04 14:10', action: '完整性校验（系统校验通过，共4/5项资料完整）' },
      { time: '2026-08-06 16:40', action: '审核退回（审核人：王财务）' },
    ],
    r3: [
      { time: '2026-08-03 10:00', action: '提交上传（刘淑芬 提交任务）' },
      { time: '2026-08-03 10:05', action: '完整性校验（系统校验通过，共2/3项资料完整）' },
      { time: '2026-08-06 10:20', action: '审核退回（审核人：陈质量）' },
    ],
    r4: [
      { time: '2026-08-06 09:30', action: '提交上传（赵宇航 提交任务）' },
      { time: '2026-08-06 09:35', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-06 10:00', action: '进入审核队列（等待分配审核人）' },
    ],
    r5: [
      { time: '2026-08-05 17:25', action: '提交上传（孙德明 提交任务）' },
      { time: '2026-08-05 17:30', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-06 09:00', action: '进入审核队列（等待分配审核人）' },
    ],
    r6: [
      { time: '2026-08-02 10:00', action: '提交上传（赵环保 提交任务）' },
      { time: '2026-08-02 10:10', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-03 14:00', action: '审核通过（审核人：赵环保）' },
    ],
    r7: [
      { time: '2026-08-01 16:00', action: '提交上传（张建国 提交任务）' },
      { time: '2026-08-01 16:05', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-03 16:10', action: '审核通过（审核人：赵环保）' },
    ],
  }
  return mockTimelines[recordId] || reviewTimeline
}

function getRequirementsForRecord(recordId: string): { text: string; status?: string }[] {
  const apiRequirements = recordRequirements.value[recordId]
  if (apiRequirements && apiRequirements.length > 0) {
    return apiRequirements.map(item => ({
      text: item.requirementText,
      status: item.status,
    }))
  }
  const mockRequirements: Record<string, { text: string; status?: string }[]> = {
    r1: [
      { text: '审批签章页缺失，请补充完整并加盖单位公章。', status: '待补正' },
      { text: '附件日期与资料周期不一致，请核对后重新上传。', status: '待补正' },
    ],
    r2: [
      { text: '工资表需加盖公章，当前扫描件公章不清晰。', status: '待补正' },
      { text: '部分附件清晰度不足，建议重新扫描后上传。', status: '待补正' },
    ],
    r3: [
      { text: '土地权属证明不完整，需补充用地批复文件。', status: '待补正' },
      { text: '临时用地范围图缺失，请补充红线图。', status: '待补正' },
    ],
  }
  return mockRequirements[recordId] || []
}

function getDeadlineForRecord(recordId: string): string {
  return recordDeadlines.value[recordId] || '2026-08-10 18:00（剩余 3 天 9 小时）'
}

function handleRectify() {
  const record = selectedRecord.value
  if (!record) return
  const taskIdMap: Record<string, string> = {
    r1: 't2',
    r2: 't3',
    r3: 't4',
  }
  const taskId = record.taskId || taskIdMap[record.id] || 't2'
  emit('openTask', taskId, '审核记录')
}

async function handleApprove() {
  const reviewId = selectedRecord.value?.id
  if (!reviewId) return

  const res = await approveReview(reviewId, {
    reviewer: '项目审核人',
    comment: '资料完整，审核通过',
  })

  if (res && res.ok) {
    showMessage(res.message || '审核通过成功', 'success')
    await reloadAll()
    emitWorkspaceRefresh({ source: 'review-action', scopes: ['summary', 'tasks', 'reviews'], reviewId })
  } else if (res && !res.ok) {
    showMessage(res.message || '审核通过失败', 'error')
  } else {
    showMessage('审核接口未响应，已保留当前展示数据', 'error')
  }
}

async function handleReturn() {
  const reviewId = selectedRecord.value?.id
  if (!reviewId) return

  if (!confirm('确认退回该审核记录？将生成补正要求。')) return

  const res = await returnReview(reviewId, {
    reviewer: '项目审核人',
    comment: '附件签章和日期信息需补正',
    requirements: [
      '请补充资料签章页。',
      '请重新上传日期清晰的扫描件。',
    ],
  })

  if (res && res.ok) {
    showMessage(res.message || '审核退回成功', 'success')
    await reloadAll()
    emitWorkspaceRefresh({ source: 'review-action', scopes: ['summary', 'tasks', 'reviews'], reviewId })
  } else if (res && !res.ok) {
    showMessage(res.message || '审核退回失败', 'error')
  } else {
    showMessage('审核接口未响应，已保留当前展示数据', 'error')
  }
}

async function reloadAll() {
  const reviewId = selectedRecord.value?.id
  await loadData()
  if (reviewId) {
    await loadReviewDetail(reviewId)
  }
}

function handleViewDetail() {
  showMessage('查看详情功能为原型预留，后续可接入任务详情页面。', 'info')
}
</script>

<template>
  <div class="workspace-review">
    <div class="page-header">
      <div class="page-title">审核结果</div>
      <div class="page-subtitle">查看提交状态、审核意见与补正要求</div>
    </div>

    <div v-if="pageMessage" :class="['page-message', pageMessageType]">
      {{ pageMessage }}
    </div>

    <div class="status-cards">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="status-card"
        :style="{ '--accent-color': card.color }"
        @click="activeTab = card.label"
      >
        <div class="card-icon">
          <Clock v-if="card.label === '待审核'" :size="20" />
          <CheckCircle v-else-if="card.label === '已通过'" :size="20" />
          <XCircle v-else-if="card.label === '已退回'" :size="20" />
          <AlertTriangle v-else-if="card.label === '补正逾期'" :size="20" />
        </div>
        <div class="card-label">{{ card.label }}</div>
        <div class="card-value">{{ card.value }}</div>
        <div class="card-unit">{{ card.unit }}</div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-section">
        <div class="tab-bar">
          <button
            v-for="tab in tabs"
            :key="tab"
            :class="{ active: activeTab === tab }"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </div>

        <div class="filter-section">
          <div class="search-box">
            <Search :size="16" />
            <input v-model="searchKeyword" type="text" placeholder="搜索任务名称" />
          </div>
          <div class="filter-group">
            <span class="filter-label">ESG模块</span>
            <select v-model="selectedModule">
              <option value="全部">全部</option>
              <option value="E">E</option>
              <option value="S">S</option>
              <option value="G">G</option>
            </select>
          </div>
          <div class="filter-group">
            <span class="filter-label">提交时间</span>
            <input v-model="startDate" type="text" placeholder="开始日期" />
            <span class="date-separator">~</span>
            <input v-model="endDate" type="text" placeholder="结束日期" />
          </div>
          <button class="reset-btn" @click="handleReset">重置</button>
        </div>

        <div class="records-table-wrapper">
          <table class="records-table">
            <thead>
              <tr>
                <th>任务名称</th>
                <th>ESG模块</th>
                <th>提交时间</th>
                <th>审核状态</th>
                <th>审核人</th>
                <th>审核意见摘要</th>
                <th>下一步</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in filteredRecords"
                :key="record.id"
                class="record-row"
                :class="{ selected: selectedRecordId === record.id }"
                @click="selectedRecordId = record.id; loadReviewDetail(record.id)"
              >
                <td class="task-name">{{ record.taskName }}</td>
                <td>
                  <span class="module-tag" :style="{ background: `${getModuleColor(record.module)}20`, color: getModuleColor(record.module) }">
                    {{ record.module }} {{ record.moduleName }}
                  </span>
                </td>
                <td>{{ record.submitTime }}</td>
                <td>
                  <span class="status-tag" :style="{ background: `${getStatusColor(record.status)}20`, color: getStatusColor(record.status) }">
                    {{ record.status }}
                  </span>
                </td>
                <td>{{ record.reviewer }}</td>
                <td class="comment-cell">{{ record.commentSummary || '-' }}</td>
                <td>
                  <button class="next-step-btn" :style="{ color: getStatusColor(record.status) }">
                    {{ record.nextStep }}
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
          <span class="total-count">共 {{ filteredRecords.length }} 条</span>
        </div>
      </div>

      <div class="right-section">
        <div class="timeline-card">
          <div class="card-header">
            <div class="card-title">审核轨迹预览</div>
          </div>
          <div class="current-task">
            <span class="task-name">{{ selectedRecord?.taskName }}</span>
            <span class="task-status" :style="{ color: getStatusColor(selectedRecord?.status || '') }">{{ selectedRecord?.status }}</span>
          </div>
          <div class="timeline">
            <div v-for="(item, index) in getTimelineForRecord(selectedRecord?.id || '')" :key="index" class="timeline-item">
              <div class="timeline-dot" :class="{ last: index === getTimelineForRecord(selectedRecord?.id || '').length - 1 }">
                <component :is="getTimelineIcon(item.action)" :size="14" />
              </div>
              <div class="timeline-content">
                <span class="timeline-time">{{ item.time }}</span>
                <span class="timeline-action">{{ item.action }}</span>
              </div>
            </div>
          </div>

          <div v-if="selectedRecord?.status === '已退回'" class="requirements-section">
            <div class="requirements-header">
              <span class="requirements-title">补正要求（{{ getRequirementsForRecord(selectedRecord?.id || '').length }}条）</span>
            </div>
            <div class="requirements-list">
              <div v-for="(req, idx) in getRequirementsForRecord(selectedRecord?.id || '')" :key="idx" class="requirement-item">
                <span class="requirement-number">{{ idx + 1 }}</span>
                <span class="requirement-text">{{ req.text }}</span>
                <span v-if="req.status" :class="['requirement-status', req.status]">
                  {{ req.status === '待补正' ? '待补正' : '已补正' }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="selectedRecord?.status === '已退回'" class="deadline-section">
            <span class="deadline-label">补正截止时间</span>
            <span class="deadline-value" style="color: #ff4f5e">{{ getDeadlineForRecord(selectedRecord?.id || '') }}</span>
          </div>

          <button 
            v-if="selectedRecord?.status === '已退回'" 
            class="rectify-btn" 
            @click="handleRectify"
          >进入补正</button>
          <div v-else-if="selectedRecord?.status === '待审核'" class="review-actions">
            <button class="review-btn return-btn" @click="handleReturn">
              <XCircle :size="16" />
              审核退回
            </button>
            <button class="review-btn approve-btn" @click="handleApprove">
              <CheckCircle :size="16" />
              审核通过
            </button>
          </div>
          <button 
            v-else 
            class="rectify-btn view-btn" 
            @click="handleViewDetail"
          >查看详情</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-review {
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

.page-subtitle {
  font-size: 13px;
  color: #8fa9c8;
  margin-top: 4px;
}

.page-message {
  margin: -6px 0 14px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.page-message.info {
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.3);
  color: #9fc7ff;
}

.page-message.success {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.page-message.error {
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  color: #ff4f5e;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
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

.main-content {
  display: flex;
  gap: 20px;
}

.left-section {
  flex: 1;
}

.right-section {
  width: 400px;
}

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
}

.tab-bar button {
  padding: 8px 20px;
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-bar button.active {
  background: rgba(255, 79, 94, 0.15);
  border-color: #ff4f5e;
  color: #ff4f5e;
}

.filter-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  margin-bottom: 16px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #8fa9c8;
  min-width: 200px;
}

.search-box input {
  background: transparent;
  border: none;
  color: #e8f3ff;
  font-size: 12px;
  flex: 1;
  outline: none;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 12px;
  color: #8fa9c8;
}

.filter-group select,
.filter-group input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  padding: 6px 10px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
}

.date-separator {
  color: #8fa9c8;
  font-size: 12px;
}

.reset-btn {
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
}

.records-table-wrapper {
  overflow-x: auto;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
}

.records-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.record-row {
  cursor: pointer;
  transition: background 0.2s;
}

.record-row:hover {
  background: rgba(105, 227, 111, 0.05);
}

.record-row.selected {
  background: rgba(105, 227, 111, 0.1);
}

.record-row td {
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

.comment-cell {
  color: #8fa9c8;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.next-step-btn {
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
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

.timeline-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.card-header {
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.current-task {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
}

.current-task .task-name {
  font-size: 13px;
  color: #e8f3ff;
}

.task-status {
  font-size: 12px;
  font-weight: 600;
}

.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: rgba(105, 227, 111, 0.2);
}

.timeline-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  position: relative;
}

.timeline-dot {
  position: absolute;
  left: -20px;
  top: 2px;
  width: 16px;
  height: 16px;
  background: rgba(105, 227, 111, 0.1);
  border: 2px solid #69e36f;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #69e36f;
}

.timeline-dot.last {
  border-color: #ff4f5e;
  color: #ff4f5e;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.timeline-time {
  font-size: 11px;
  color: #5a7a9a;
}

.timeline-action {
  font-size: 12px;
  color: #e8f3ff;
}

.requirements-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(105, 227, 111, 0.1);
}

.requirements-header {
  margin-bottom: 12px;
}

.requirements-title {
  font-size: 12px;
  color: #ff4f5e;
  font-weight: 600;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.requirement-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  align-items: center;
}

.requirement-number {
  width: 20px;
  height: 20px;
  background: rgba(255, 79, 94, 0.2);
  border: 1px solid rgba(255, 79, 94, 0.4);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #ff4f5e;
  flex-shrink: 0;
}

.requirement-text {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.5;
  flex: 1;
}

.requirement-status {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  flex-shrink: 0;
}

.requirement-status.待补正 {
  background: rgba(255, 179, 71, 0.2);
  color: #ffb347;
  border: 1px solid rgba(255, 179, 71, 0.3);
}

.requirement-status.已补正 {
  background: rgba(105, 227, 111, 0.2);
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.3);
}

.deadline-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 8px;
  margin-top: 16px;
}

.deadline-label {
  font-size: 12px;
  color: #8fa9c8;
}

.deadline-value {
  font-size: 12px;
  font-weight: 600;
}

.rectify-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  border-radius: 8px;
  color: #031020;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 16px;
}

.rectify-btn.view-btn {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.review-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.review-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.review-btn:active {
  transform: scale(0.97);
  transition-duration: 0.08s;
}

.return-btn {
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  color: #ff4f5e;
}

.approve-btn {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  color: #031020;
}
</style>
