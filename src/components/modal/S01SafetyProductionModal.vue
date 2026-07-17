<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { Check, ShieldCheck, X } from 'lucide-vue-next'
import { getDashboardKpiS01 } from '@/services/api'

type CountingStatus = 'continuous' | 'interrupted' | 'pending'

interface SafetyProductionData {
  projectStartDate: string
  currentDate: string
  currentStage: string
  currentStageDetail: string
  countingStatus: CountingStatus
  latestInterruptDate?: string
  latestInterruptReason?: string
  updateTime: string
}

interface ConstructionStage {
  id: string
  name: string
  status: 'completed' | 'current' | 'not_started'
  detail?: string
  startDate?: string
  endDate?: string
}

const emit = defineEmits<{
  (e: 'close'): void
}>()

const mockSafetyProductionData: SafetyProductionData = {
  projectStartDate: '2025-07-10',
  currentDate: '2026-07-13',
  currentStage: '主体工程施工',
  currentStageDetail: '路基｜桥梁｜隧道并行施工',
  countingStatus: 'continuous',
  updateTime: '2026-07-13 10:30',
}

const mockConstructionStages: ConstructionStage[] = [
  {
    id: 'preparation',
    name: '施工准备',
    status: 'completed',
  },
  {
    id: 'main-construction',
    name: '主体工程施工',
    status: 'current',
    detail: '路基｜桥梁｜隧道并行施工',
  },
  {
    id: 'pavement',
    name: '路面及附属工程',
    status: 'not_started',
  },
  {
    id: 'handover',
    name: '交工验收',
    status: 'not_started',
  },
]

const safetyProductionData = ref<SafetyProductionData>(mockSafetyProductionData)
const constructionStages = ref<ConstructionStage[]>(mockConstructionStages)
const conclusionText = ref('项目开工以来，未发生导致连续安全生产记录中断的事故，当前已连续安全生产368天。')

const showAccidentToast = ref(false)
let accidentToastTimer: ReturnType<typeof setTimeout> | null = null

function toUtcDate(dateText: string) {
  const [year, month, day] = dateText.split('-').map(Number)
  return Date.UTC(year, month - 1, day)
}

function calculateContinuousDays(data: SafetyProductionData) {
  const cycleStartDate = data.latestInterruptDate ?? data.projectStartDate
  const start = toUtcDate(cycleStartDate)
  const current = toUtcDate(data.currentDate)
  return Math.max(0, Math.floor((current - start) / 86_400_000))
}

function buildMonthTicks(startDate: string, endDate: string) {
  const [startYear, startMonth] = startDate.split('-').map(Number)
  const [endYear, endMonth] = endDate.split('-').map(Number)
  const ticks: string[] = []
  let year = startYear
  let month = startMonth

  while (year < endYear || (year === endYear && month <= endMonth)) {
    ticks.push(`${year}-${String(month).padStart(2, '0')}`)
    month += 1
    if (month > 12) {
      month = 1
      year += 1
    }
  }

  return ticks
}

const continuousDays = computed(() => calculateContinuousDays(safetyProductionData.value))
const monthTicks = computed(() => buildMonthTicks(safetyProductionData.value.projectStartDate, safetyProductionData.value.currentDate))

const statusLabel = computed(() => {
  if (safetyProductionData.value.countingStatus === 'interrupted') return '计数中断'
  if (safetyProductionData.value.countingStatus === 'pending') return '待复核'
  return '连续计数中'
})

const statusClass = computed(() => safetyProductionData.value.countingStatus)

async function loadData() {
  const data = await getDashboardKpiS01()
  if (data) {
    safetyProductionData.value = {
      projectStartDate: data.projectStartDate,
      currentDate: data.currentDate,
      currentStage: data.currentStage,
      currentStageDetail: data.currentStageDetail,
      countingStatus: data.countingStatus as CountingStatus,
      latestInterruptDate: data.latestInterruptDate,
      latestInterruptReason: data.latestInterruptReason,
      updateTime: data.updateTime,
    }
    if (data.constructionStages) {
      constructionStages.value = data.constructionStages.map(s => ({
        id: s.id,
        name: s.name,
        status: s.status === 'current' ? 'current' : s.status === 'completed' ? 'completed' : 'not_started',
        detail: s.detail,
      }))
    }
    if (data.conclusion) {
      conclusionText.value = data.conclusion
    }
  }
}

function handleViewAccidentRecords() {
  showAccidentToast.value = true
  if (accidentToastTimer) clearTimeout(accidentToastTimer)
  accidentToastTimer = setTimeout(() => {
    showAccidentToast.value = false
    accidentToastTimer = null
  }, 2600)
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="s01-modal-overlay" @click="emit('close')">
    <section class="s01-modal" role="dialog" aria-modal="true" aria-labelledby="s01-modal-title" @click.stop>
      <header class="s01-header">
        <h2 id="s01-modal-title" class="s01-title">
          <span class="s01-key">S01</span>
          <span>连续安全生产天数</span>
        </h2>
        <div class="s01-header-actions">
          <span class="counting-status" :class="statusClass">
            <i />
            {{ statusLabel }}
          </span>
          <button class="close-icon" aria-label="关闭" @click="emit('close')">
            <X :size="21" />
          </button>
        </div>
      </header>

      <main class="s01-body">
        <section class="core-panel">
          <div class="core-item hero">
            <div class="core-label">当前连续安全生产周期</div>
            <div class="hero-value">
              <span class="hero-number">{{ continuousDays }}</span>
              <span class="hero-unit">天</span>
            </div>
          </div>
          <div class="core-divider" />
          <div class="core-item">
            <div class="core-label">开工日期</div>
            <div class="core-value">{{ safetyProductionData.projectStartDate }}</div>
          </div>
          <div class="core-divider" />
          <div class="core-item">
            <div class="core-label">当前日期</div>
            <div class="core-value">{{ safetyProductionData.currentDate }}</div>
          </div>
          <div class="core-divider" />
          <div class="core-item stage">
            <div class="core-label">当前工期阶段</div>
            <div class="core-value">{{ safetyProductionData.currentStage }}</div>
          </div>
        </section>

        <section class="timeline-panel">
          <h3>连续安全生产时间流程</h3>
          <div class="safe-timeline">
            <div class="timeline-main-row">
              <div class="timeline-endpoint start">
                <span>开工日期</span>
                <strong>{{ safetyProductionData.projectStartDate }}</strong>
              </div>
              <div class="safe-line-wrap">
                <div class="safe-line" :class="{ interrupted: safetyProductionData.countingStatus === 'interrupted' }">
                  <div class="line-node left" />
                  <div v-if="safetyProductionData.countingStatus === 'interrupted'" class="interrupt-node">
                    <span>{{ safetyProductionData.latestInterruptDate }}</span>
                  </div>
                  <div class="line-message">本轮连续周期内无事故中断</div>
                  <div class="line-node right" />
                </div>
              </div>
              <div class="timeline-endpoint current">
                <span>当前</span>
                <strong>{{ safetyProductionData.currentDate }}</strong>
                <em>{{ continuousDays }}天</em>
              </div>
            </div>
            <div class="month-axis">
              <span v-for="month in monthTicks" :key="month">{{ month }}</span>
            </div>
          </div>
        </section>

        <section class="stage-panel">
          <h3>工期流程</h3>
          <div class="stage-flow">
            <div
              v-for="(stage, index) in constructionStages"
              :key="stage.id"
              class="stage-node"
              :class="stage.status"
            >
              <div v-if="index < constructionStages.length - 1" class="stage-connector" :class="stage.status" />
              <div class="stage-circle">
                <Check v-if="stage.status === 'completed'" :size="22" />
              </div>
              <div class="stage-name">{{ stage.name }}</div>
              <div class="stage-status">
                {{ stage.status === 'completed' ? '已完成' : stage.status === 'current' ? '进行中' : '未开始' }}
              </div>
              <div v-if="stage.detail" class="stage-detail">{{ stage.detail }}</div>
            </div>
          </div>
        </section>

        <section class="conclusion-card">
          <div class="conclusion-icon">
            <ShieldCheck :size="20" />
          </div>
          <div class="conclusion-content">
            <h3>本轮结论</h3>
            <p>{{ conclusionText }}</p>
          </div>
        </section>
      </main>

      <footer class="s01-footer">
        <div class="data-time">数据截至：{{ safetyProductionData.updateTime }}</div>
        <div class="footer-actions">
          <button class="secondary-btn" @click="handleViewAccidentRecords">查看事故记录</button>
          <button class="primary-btn" @click="emit('close')">关闭</button>
        </div>
      </footer>

      <Transition name="s01-toast">
        <div v-if="showAccidentToast" class="accident-toast">
          事故记录列表接口已预留；当前暂无导致连续安全生产记录中断的事故。
        </div>
      </Transition>
    </section>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.s01-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(1, 8, 20, 0.68);
  backdrop-filter: blur(4px);
}

.s01-modal {
  position: relative;
  width: 68vw;
  max-width: 1280px;
  height: 80vh;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #e8f3ff;
  background: linear-gradient(180deg, rgba(7, 22, 44, 0.96) 0%, rgba(5, 18, 38, 0.96) 100%);
  border: 1px solid rgba(47, 156, 255, 0.4);
  border-radius: 6px;
  box-shadow:
    0 0 0 1px rgba(47, 156, 255, 0.35),
    0 20px 60px rgba(0, 0, 0, 0.6);
}

.s01-header {
  height: 52px;
  flex: 0 0 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.12);
  flex-shrink: 0;
}

.s01-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.s01-key {
  font-family: var(--font-num);
  color: #2f9cff;
  font-size: 26px;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(47, 156, 255, 0.4);
}

.s01-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.counting-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  border: 1px solid rgba(105, 227, 111, 0.6);
  color: #69e36f;
  background: rgba(105, 227, 111, 0.08);
}

.counting-status i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #69e36f;
  box-shadow: 0 0 8px rgba(105, 227, 111, 0.7);
}

.counting-status.interrupted {
  color: #ff4f5e;
  border-color: rgba(255, 79, 94, 0.6);
  background: rgba(255, 79, 94, 0.08);
}

.counting-status.interrupted i {
  background: #ff4f5e;
  box-shadow: 0 0 8px rgba(255, 79, 94, 0.7);
}

.counting-status.pending {
  color: #ffb347;
  border-color: rgba(255, 179, 71, 0.6);
  background: rgba(255, 179, 71, 0.08);
}

.counting-status.pending i {
  background: #ffb347;
  box-shadow: 0 0 8px rgba(255, 179, 71, 0.7);
}

.close-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(143, 169, 200, 0.28);
  border-radius: 4px;
  color: #d7e8ff;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.s01-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 18px;
  overflow: hidden;
}

.core-panel,
.timeline-panel,
.stage-panel,
.conclusion-card {
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(143, 169, 200, 0.12);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
}

.core-panel {
  flex: 0 0 96px;
  display: grid;
  grid-template-columns: 1.2fr 1px 0.8fr 1px 0.8fr 1px 0.9fr;
  align-items: center;
  padding: 0 20px;
}

.core-item {
  min-width: 0;
}

.core-item.hero {
  align-self: stretch;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.core-divider {
  width: 1px;
  height: 44px;
  background: linear-gradient(180deg, transparent, rgba(143, 169, 200, 0.25), transparent);
}

.core-label {
  margin-bottom: 4px;
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
}

.core-value {
  font-family: var(--font-num);
  color: #2f9cff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.3px;
  text-shadow: 0 0 6px rgba(47, 156, 255, 0.35);
}

.core-item.stage .core-value {
  font-size: 22px;
}

.hero-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.hero-number {
  font-family: var(--font-num);
  color: #2f9cff;
  font-size: 44px;
  line-height: 0.95;
  font-weight: 700;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(47, 156, 255, 0.5), 0 0 20px rgba(47, 156, 255, 0.3);
}

.hero-unit {
  color: #d7e8ff;
  font-size: 14px;
  font-weight: 600;
}

.timeline-panel {
  flex: 0 0 132px;
  padding: 8px 14px;
}

.stage-panel {
  flex: 0 0 120px;
  padding: 8px 14px;
}

.timeline-panel h3,
.stage-panel h3 {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

.safe-timeline {
  position: relative;
}

.timeline-main-row {
  display: grid;
  grid-template-columns: 90px 1fr 100px;
  align-items: center;
  gap: 10px;
}

.timeline-endpoint {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  font-weight: 600;
}

.timeline-endpoint span {
  color: #e8f3ff;
}

.timeline-endpoint strong {
  color: #69e36f;
  font-size: 13px;
}

.timeline-endpoint.current strong,
.timeline-endpoint.current em {
  color: #2f9cff;
}

.timeline-endpoint.current em {
  font-style: normal;
  font-size: 16px;
  font-weight: 700;
}

.safe-line-wrap {
  position: relative;
  height: 30px;
}

.safe-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 15px;
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, #69e36f, #79f083);
  box-shadow: 0 0 10px rgba(105, 227, 111, 0.55);
}

.safe-line.interrupted {
  background: linear-gradient(90deg, #69e36f 0%, #69e36f 55%, #ff4f5e 56%, #ff4f5e 58%, #69e36f 59%, #69e36f 100%);
}

.line-node {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #69e36f;
  transform: translateY(-50%);
  box-shadow: 0 0 10px rgba(105, 227, 111, 0.65);
}

.line-node.left {
  left: -1px;
}

.line-node.right {
  right: -1px;
}

.line-message {
  position: absolute;
  left: 50%;
  top: -16px;
  transform: translateX(-50%);
  color: #69e36f;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.interrupt-node {
  position: absolute;
  left: 56%;
  top: 50%;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ff4f5e;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 10px rgba(255, 79, 94, 0.6);
}

.interrupt-node span {
  position: absolute;
  left: 50%;
  top: 20px;
  transform: translateX(-50%);
  color: #ff4f5e;
  font-size: 10px;
  white-space: nowrap;
}

.month-axis {
  display: grid;
  grid-template-columns: repeat(13, minmax(0, 1fr));
  margin: 6px 90px 0 100px;
  border-top: 1px dashed rgba(143, 169, 200, 0.18);
}

.month-axis span {
  position: relative;
  padding-top: 4px;
  color: #778aa5;
  font-size: 9px;
  text-align: center;
}

.month-axis span::before {
  content: '';
  position: absolute;
  top: -7px;
  left: 50%;
  width: 1px;
  height: 7px;
  background: rgba(143, 169, 200, 0.22);
}

.stage-flow {
  position: relative;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  align-items: start;
  padding: 8px 36px 0;
}

.stage-node {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 68px;
}

.stage-connector {
  position: absolute;
  top: 14px;
  left: calc(50% + 18px);
  width: calc(100% - 36px);
  height: 4px;
  background: rgba(143, 169, 200, 0.2);
}

.stage-connector.completed {
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  box-shadow: 0 0 8px rgba(47, 156, 255, 0.22);
}

.stage-connector.current {
  background: rgba(143, 169, 200, 0.2);
}

.stage-circle {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid rgba(143, 169, 200, 0.4);
  background: rgba(255, 255, 255, 0.03);
  color: #e8f3ff;
}

.stage-node.completed .stage-circle {
  color: #fff;
  border-color: #69e36f;
  background: rgba(105, 227, 111, 0.15);
  box-shadow: 0 0 12px rgba(105, 227, 111, 0.5);
}

.stage-node.current .stage-circle {
  border-color: #2f9cff;
  background: rgba(47, 156, 255, 0.15);
  box-shadow: 0 0 10px rgba(47, 156, 255, 0.5), inset 0 0 0 4px rgba(47, 156, 255, 0.15);
}

.stage-name {
  margin-top: 6px;
  color: #f4f8ff;
  font-size: 12px;
  font-weight: 700;
}

.stage-status {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 600;
}

.stage-node.completed .stage-status {
  color: #69e36f;
}

.stage-node.current .stage-status,
.stage-detail {
  color: #2f9cff;
}

.stage-detail {
  margin-top: 2px;
  font-size: 10px;
  font-weight: 600;
}

.conclusion-card {
  flex: 0 0 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  background: rgba(105, 227, 111, 0.06);
}

.conclusion-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  background: rgba(105, 227, 111, 0.12);
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.25);
}

.conclusion-content {
  flex: 1;
  min-width: 0;
}

.conclusion-card h3 {
  margin: 0 0 2px;
  color: #69e36f;
  font-size: 13px;
  font-weight: 700;
}

.conclusion-card p {
  margin: 0;
  color: #f4f8ff;
  font-size: 12px;
  line-height: 1.3;
  font-weight: 600;
}

.s01-footer {
  height: 44px;
  flex: 0 0 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  border-top: 1px solid rgba(143, 169, 200, 0.12);
  flex-shrink: 0;
}

.data-time {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.secondary-btn,
.primary-btn {
  min-width: 100px;
  height: 32px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.secondary-btn {
  color: #e8f3ff;
  border: 1px solid rgba(47, 156, 255, 0.6);
  background: rgba(255, 255, 255, 0.03);
}

.primary-btn {
  color: #fff;
  border: 1px solid #2f9cff;
  background: linear-gradient(135deg, #0b67d8, #1794ff);
  box-shadow: 0 0 10px rgba(47, 156, 255, 0.25);
}

.accident-toast {
  position: absolute;
  left: 50%;
  bottom: 50px;
  transform: translateX(-50%);
  padding: 8px 14px;
  border: 1px solid rgba(47, 156, 255, 0.5);
  border-radius: 4px;
  color: #d7e8ff;
  background: rgba(5, 18, 38, 0.96);
  font-size: 12px;
  box-shadow: 0 0 10px rgba(47, 156, 255, 0.15);
}

.s01-toast-enter-active,
.s01-toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.s01-toast-enter-from,
.s01-toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}
</style>
