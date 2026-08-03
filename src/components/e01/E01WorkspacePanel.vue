<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE01Events } from '@/services/api'
import type {
  E01CategoryFilter,
  E01EventsPayload,
  E01OpenPoint,
  E01PanelLayer,
} from '@/types/e01'
import { formatSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedPointId: number | null
  layer: E01PanelLayer
  categoryFilter: E01CategoryFilter
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E01CategoryFilter]
  selectPoint: [point: E01OpenPoint]
  clearSelection: []
  overviewReady: [points: E01OpenPoint[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E01EventsPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  totalOpenPoints: 0,
  waterCount: 0,
  airCount: 0,
  noiseCount: 0,
})

const openPoints = computed(() => payload.value?.openPoints || [])

const filteredPoints = computed(() => {
  if (props.categoryFilter === 'ALL') return openPoints.value
  return openPoints.value.filter((p) => p.monitorCategory === props.categoryFilter)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredPoints.value.length / PAGE_SIZE)))

const pagedPoints = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredPoints.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredPoints.value.length} 处 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredPoints.value.length > PAGE_SIZE)

const categoryTabs = computed(() => [
  { key: 'ALL' as const, label: '超标总计', value: overview.value.totalOpenPoints },
  { key: 'WATER' as const, label: '水质', value: overview.value.waterCount },
  { key: 'AIR' as const, label: '环境空气', value: overview.value.airCount },
  { key: 'NOISE' as const, label: '噪声', value: overview.value.noiseCount },
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

function sectionLabel(point: E01OpenPoint) {
  return formatSectionLabel(point.sectionCode || point.sectionName)
}

function typeLabel(point: E01OpenPoint) {
  const map: Record<string, string> = {
    WATER: '水质监测点',
    AIR: '扬尘监测点',
    NOISE: '噪声监测点',
  }
  return map[point.monitorCategory] || `${point.monitorCategoryLabel}监测点`
}

function typeLine(point: E01OpenPoint) {
  return typeWithSection(typeLabel(point), sectionLabel(point))
}

function factorNames(point: E01OpenPoint) {
  return point.factors.map((f) => f.factorName).filter(Boolean).join('/') || '—'
}

function primaryFactor(point: E01OpenPoint) {
  return point.factors[0] || null
}

function valueText(value: unknown, unit?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return unit ? `${text} ${unit}` : text
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE01Events()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E01 事件数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.openPoints || [])
  } catch {
    error.value = 'E01 事件数据加载失败'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleCategoryClick(key: E01CategoryFilter) {
  if (props.categoryFilter === key) {
    emit('clearSelection')
    emit('changeCategory', key)
    return
  }
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectPoint(point: E01OpenPoint) {
  emit('selectPoint', point)
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

watch(filteredPoints, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, openPoints })
</script>

<template>
  <aside class="e01-panel e01-panel--green">
    <header class="e01-head">
      <h2>环境影响事件</h2>
      <button type="button" class="e01-close" aria-label="关闭E01" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e01-state">正在加载…</div>
    <div v-else-if="error" class="e01-state is-error">{{ error }}</div>
    <template v-else>
      <section class="e01-stats" aria-label="超标分类统计">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e01-stats__cell"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </button>
      </section>

      <div class="e01-list-title">当前超标点位</div>

      <div class="e01-list">
        <button
          v-for="point in pagedPoints"
          :key="point.pointId"
          type="button"
          class="e01-row"
          :class="{ active: selectedPointId === point.pointId, 'no-locate': !point.canLocate }"
          @click="handleSelectPoint(point)"
        >
          <div class="e01-row__top">
            <span class="e01-row__type">{{ typeLine(point) }}</span>
            <em class="e01-row__status">{{ point.status }}</em>
          </div>
          <div class="e01-row__loc">{{ point.locationText || point.pointName }}</div>
          <div class="e01-row__factor">
            <b>{{ factorNames(point) }}</b>
            <span>
              实测
              <i>{{ valueText(primaryFactor(point)?.detectedValue, primaryFactor(point)?.unit) }}</i>
            </span>
            <span class="muted">
              限值 {{ valueText(primaryFactor(point)?.limitValue, primaryFactor(point)?.unit) }}
            </span>
            <span
              v-if="primaryFactor(point)?.exceedMultiple != null"
              class="e01-row__multi"
            >
              超标 {{ primaryFactor(point)?.exceedMultiple }}倍
            </span>
          </div>
          <div class="e01-row__foot">
            <span>{{ dateOnly(point.discoveredAt) }}</span>
            <span v-if="!point.canLocate" class="warn">无法定位</span>
          </div>
        </button>

        <p v-if="!pagedPoints.length" class="e01-empty">当前分类暂无未闭环超标点位</p>
      </div>

      <nav class="e01-pager" aria-label="点位分页">
        <span class="e01-pager__summary">{{ pagerSummary }}</span>
        <div v-if="showPageControls" class="e01-pager__controls">
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
.e01-panel {
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

.e01-head {
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
    &::after {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
      margin-left: 8px;
      border-radius: 50%;
      background: #69e36f;
      box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.18);
      vertical-align: middle;
    }
  }
}

.e01-close {
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

.e01-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.e01-stats {
  flex-shrink: 0;
  height: 58px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 12px;
  overflow: hidden;
}

.e01-stats__cell {
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

.e01-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.e01-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.e01-row {
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

.e01-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.e01-row__type {
  font-size: 14px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e01-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 1px 6px;
  background: rgba(105, 227, 111, 0.08);
}

.e01-row__loc {
  margin-top: 5px;
  font-size: 15px;
  color: #e8f3ff;
  line-height: 1.4;
}

.e01-row__factor {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: baseline;
  font-size: 13px;
  color: #8ba6c3;

  b {
    font-size: 14px;
    font-weight: 600;
    color: #f3f8ff;
  }

  i {
    font-style: normal;
    color: #ff8f5a;
    font-weight: 700;
    font-size: 15px;
  }

  .muted { color: #7f95ad; font-size: 13px; }
}

.e01-row__multi {
  color: #ff8f5a;
  font-weight: 600;
  font-size: 12px;
  border: 1px solid rgba(255, 143, 90, 0.35);
  border-radius: 3px;
  padding: 0 5px;
  line-height: 18px;
}

.e01-row__foot {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #7f95ad;

  .warn { color: #ff9f2f; }
}

.e01-empty {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;
}

.e01-pager {
  flex-shrink: 0;
  margin-top: 10px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.e01-pager__summary {
  font-size: 13px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e01-pager__controls {
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
