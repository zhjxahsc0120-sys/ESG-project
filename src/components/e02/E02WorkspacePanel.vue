<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE02Issues } from '@/services/api'
import type {
  E02CategoryFilter,
  E02IssueItem,
  E02IssuesPayload,
  E02PanelLayer,
} from '@/types/e02'
import {
  extractSectionLabel,
  stripSectionPrefix,
  typeWithSection,
} from '@/utils/section-label'

const props = defineProps<{
  selectedIssueId: number | null
  layer: E02PanelLayer
  categoryFilter: E02CategoryFilter
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E02CategoryFilter]
  selectIssue: [issue: E02IssueItem]
  clearSelection: []
  overviewReady: [issues: E02IssueItem[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E02IssuesPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  total: 0,
  rectifying: 0,
  pendingReview: 0,
  pendingClosure: 0,
  overdueAmong: 0,
})

function issueSection(issue: E02IssueItem) {
  return extractSectionLabel(issue.title, issue.locationText) || '未分区'
}

function issueTypeLine(issue: E02IssueItem) {
  return typeWithSection(issue.issueType || '环保问题', issueSection(issue))
}

function issueTitle(issue: E02IssueItem) {
  return stripSectionPrefix(issue.title) || issue.title || '—'
}

function issueLocation(issue: E02IssueItem) {
  return stripSectionPrefix(issue.locationText) || issue.locationText || '—'
}

const issues = computed(() => payload.value?.issues || [])

/** 一级筛选 key → API statusGroup（勿用 toLowerCase：PENDING_REVIEW ≠ pending_review） */
const STATUS_GROUP_BY_FILTER: Record<Exclude<E02CategoryFilter, 'ALL'>, string> = {
  RECTIFYING: 'rectifying',
  PENDING_REVIEW: 'pendingReview',
  PENDING_CLOSURE: 'pendingClosure',
}

const filteredIssues = computed(() => {
  if (props.categoryFilter === 'ALL') return issues.value
  const group = STATUS_GROUP_BY_FILTER[props.categoryFilter]
  return issues.value.filter((i) => i.statusGroup === group)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredIssues.value.length / PAGE_SIZE)))

const pagedIssues = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredIssues.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredIssues.value.length} 项 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredIssues.value.length > PAGE_SIZE)

const categoryTabs = computed(() => [
  { key: 'ALL' as const, label: '全部', value: overview.value.total },
  { key: 'RECTIFYING' as const, label: '整改中', value: overview.value.rectifying },
  { key: 'PENDING_REVIEW' as const, label: '待复查', value: overview.value.pendingReview },
  { key: 'PENDING_CLOSURE' as const, label: '待销项', value: overview.value.pendingClosure },
])

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return null
  return String(value)
}

function dateOnly(value?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return text.slice(0, 10)
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE02Issues()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E02 数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.issues || [])
  } catch {
    error.value = 'E02 数据加载失败'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleCategoryClick(key: E02CategoryFilter) {
  if (props.categoryFilter === key) {
    emit('clearSelection')
    emit('changeCategory', key)
    return
  }
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectIssue(issue: E02IssueItem) {
  emit('selectIssue', issue)
}

function goPage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
}

watch(
  () => props.categoryFilter,
  () => {
    page.value = 1
  },
)

watch(filteredIssues, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, issues })
</script>

<template>
  <aside class="e02-panel">
    <header class="e02-head">
      <h2>未闭环环保问题</h2>
      <button type="button" class="e02-close" aria-label="关闭E02" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e02-state">正在加载…</div>
    <div v-else-if="error" class="e02-state is-error">
      {{ error }}
      <button class="e02-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e02-stats" aria-label="状态分类统计">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e02-stats__cell"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </button>
      </section>

      <div v-if="overview.overdueAmong > 0" class="e02-overdue-hint">
        其中逾期 <strong>{{ overview.overdueAmong }}</strong> 项
      </div>

      <div class="e02-list-title">当前未闭环事项</div>

      <div class="e02-list">
        <button
          v-for="issue in pagedIssues"
          :key="issue.id"
          type="button"
          class="e02-row"
          :class="{ active: selectedIssueId === issue.id, 'no-locate': !issue.canLocate }"
          @click="handleSelectIssue(issue)"
        >
          <div class="e02-row__top">
            <span class="e02-row__type">{{ issueTypeLine(issue) }}</span>
            <em class="e02-row__status" :class="{ overdue: issue.overdue }">{{ issue.status }}</em>
          </div>
          <div class="e02-row__title">{{ issueTitle(issue) }}</div>
          <div class="e02-row__loc">{{ issueLocation(issue) }}</div>
          <div class="e02-row__meta">
            <span>责任单位：{{ issue.responsibleOrgName || '—' }}</span>
            <span class="e02-row__deadline" :class="{ overdue: issue.overdue }">
              期限：{{ dateOnly(issue.deadline) }}
            </span>
          </div>
          <div v-if="!issue.canLocate" class="e02-row__foot">
            <span class="warn">无法定位</span>
          </div>
        </button>

        <p v-if="!pagedIssues.length" class="e02-empty">当前筛选暂无未闭环事项</p>
      </div>

      <nav class="e02-pager" aria-label="事项分页">
        <span class="e02-pager__summary">{{ pagerSummary }}</span>
        <div v-if="showPageControls" class="e02-pager__controls">
          <button type="button" :disabled="page <= 1" @click="goPage(page - 1)">‹</button>
          <button
            v-for="n in totalPages"
            :key="n"
            type="button"
            :class="{ active: page === n }"
            @click="goPage(n)"
          >
            {{ n }}
          </button>
          <button type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">›</button>
        </div>
      </nav>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.e02-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 14px 10px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.96);
  color: #d7e6f5;
  overflow: hidden;
}

.e02-head {
  flex-shrink: 0;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;

  h2 {
    margin: 0;
    font-size: 19px;
    font-weight: 700;
    color: #f3f8ff;
    display: flex;
    align-items: center;
    gap: 8px;

    &::before {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #69e36f;
      box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.18);
    }
  }
}

.e02-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  line-height: 1;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}

.e02-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.e02-retry {
  display: block;
  margin: 10px auto 0;
  padding: 4px 14px;
  font-size: 13px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}

.e02-stats {
  flex-shrink: 0;
  height: 58px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 10px;
  overflow: hidden;
}

.e02-stats__cell {
  border: 0;
  border-right: 1px solid rgba(105, 227, 111, 0.16);
  background: transparent;
  color: #8ba6c3;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  position: relative;

  &:last-child { border-right: 0; }

  span {
    font-size: 13px;
    line-height: 1.2;
  }

  strong {
    font-size: 21px;
    line-height: 1.1;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    color: #d7e6f5;
    font-weight: 700;
  }

  &.active {
    color: #c8f5cb;
    strong { color: #69e36f; }
    &::after {
      content: '';
      position: absolute;
      left: 18%;
      right: 18%;
      bottom: 0;
      height: 2px;
      background: #69e36f;
    }
  }
}

.e02-overdue-hint {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 12px;
  color: #ff9f2f;

  strong {
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    font-weight: 700;
  }
}

.e02-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.e02-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.e02-row {
  flex-shrink: 0;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.45);
  color: inherit;
  cursor: pointer;
  padding: 10px 10px 10px 12px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 8px;
    bottom: 8px;
    width: 2px;
    border-radius: 2px;
    background: transparent;
  }

  &:hover {
    border-color: rgba(105, 227, 111, 0.45);
    background: rgba(12, 52, 42, 0.35);
  }

  &.active {
    border-color: rgba(105, 227, 111, 0.7);
    background: rgba(24, 70, 48, 0.35);
    &::before { background: #69e36f; }
  }
}

.e02-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.e02-row__type {
  font-size: 14px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e02-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 1px 6px;
  background: rgba(105, 227, 111, 0.08);

  &.overdue {
    color: #ff9f2f;
    border-color: rgba(255, 159, 47, 0.45);
    background: rgba(255, 159, 47, 0.08);
  }
}

.e02-row__title {
  margin-top: 5px;
  font-size: 15px;
  font-weight: 600;
  color: #e8f3ff;
  line-height: 1.4;
}

.e02-row__loc {
  margin-top: 3px;
  font-size: 13px;
  color: #8ba6c3;
}

.e02-row__meta {
  margin-top: 5px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #7f95ad;
}

.e02-row__deadline {
  &.overdue { color: #ff9f2f; font-weight: 600; }
}

.e02-row__foot {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #7f95ad;

  .warn { color: #ff9f2f; }
}

.e02-empty {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;
}

.e02-pager {
  flex-shrink: 0;
  margin-top: 10px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.e02-pager__summary {
  font-size: 13px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e02-pager__controls {
  display: flex;
  gap: 6px;

  button {
    min-width: 28px;
    height: 28px;
    border: 1px solid rgba(105, 227, 111, 0.28);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.5);
    color: #8ba6c3;
    cursor: pointer;
    font-size: 13px;

    &.active {
      color: #69e36f;
      border-color: rgba(105, 227, 111, 0.7);
      background: rgba(105, 227, 111, 0.12);
    }

    &:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }
  }
}
</style>
