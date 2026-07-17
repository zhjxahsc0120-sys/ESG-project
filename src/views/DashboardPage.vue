<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import type { KpiKey, KpiDetailConfig, KpiModalFocusContext } from '@/types/dashboard'
import { kpiDetails, carbonTopicDetail, monthlyTopicDetail } from '@/data/dashboard.mock'
import { getDashboardKpiDetail, getDashboardTopic } from '@/services/api'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import TopKpiGroups from '@/components/kpi/TopKpiGroups.vue'
import GisOverviewPanel from '@/components/gis/GisOverviewPanel.vue'
import GisOverviewCesiumPanel from '@/components/gis/GisOverviewCesiumPanel.vue'
import { gisConfig } from '@/config/gis.config'
import ComplianceRiskPanel from '@/components/panels/ComplianceRiskPanel.vue'
import CarbonBenefitPanel from '@/components/panels/CarbonBenefitPanel.vue'
import MonthlyReportPanel from '@/components/panels/MonthlyReportPanel.vue'
import ConstructionTimeline from '@/components/panels/ConstructionTimeline.vue'
import KpiDetailModal from '@/components/modal/KpiDetailModal.vue'

const SCREEN_WIDTH = 1920
const SCREEN_HEIGHT = 1080

const windowWidth = ref(SCREEN_WIDTH)
const windowHeight = ref(SCREEN_HEIGHT)

const scale = computed(() => {
  const scaleX = windowWidth.value / SCREEN_WIDTH
  const scaleY = windowHeight.value / SCREEN_HEIGHT
  return Math.min(scaleX, scaleY)
})

const translateX = computed(() => {
  const scaledWidth = SCREEN_WIDTH * scale.value
  return (windowWidth.value - scaledWidth) / 2
})

const translateY = computed(() => {
  const scaledHeight = SCREEN_HEIGHT * scale.value
  return (windowHeight.value - scaledHeight) / 2
})

function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

const activeKpiKey = ref<KpiKey | null>(null)
const activeTopicDetail = ref<KpiDetailConfig | null>(null)
const apiKpiDetails = ref<Partial<Record<KpiKey, KpiDetailConfig>>>({})
const kpiFocusContext = ref<KpiModalFocusContext | null>(null)

const isKpiModalOpen = computed(() => activeKpiKey.value !== null || activeTopicDetail.value !== null)
const activeDetail = computed(() => {
  if (activeTopicDetail.value) return activeTopicDetail.value
  if (activeKpiKey.value) return apiKpiDetails.value[activeKpiKey.value] || kpiDetails[activeKpiKey.value]
  return null
})

let bodyOverflow = ''

async function handleKpiSelect(key: string) {
  const kpiKey = key as KpiKey
  if (kpiDetails[kpiKey]) {
    if (kpiKey !== 'S01') {
      const detail = await getDashboardKpiDetail(kpiKey)
      if (detail) {
        apiKpiDetails.value[kpiKey] = detail
      }
    }
    kpiFocusContext.value = null
    activeKpiKey.value = kpiKey
    activeTopicDetail.value = null
    lockBodyScroll()
  }
}

async function openKpiFromBusinessLink(payload: {
  targetType: 'E02' | 'S02'
  sourceId: string
  sourceTable?: string
  gisFeatureId?: string
  title?: string
}) {
  const kpiKey = payload.targetType as KpiKey
  if (!kpiDetails[kpiKey]) return
  if (kpiKey !== 'S01') {
    const detail = await getDashboardKpiDetail(kpiKey)
    if (detail) {
      apiKpiDetails.value[kpiKey] = detail
    }
  }
  kpiFocusContext.value = {
    sourceId: payload.sourceId,
    sourceTable: payload.sourceTable,
    gisFeatureId: payload.gisFeatureId,
    from: 'gis',
    title: payload.title,
  }
  activeKpiKey.value = kpiKey
  activeTopicDetail.value = null
  lockBodyScroll()
}

async function handleTopicSelect(topicKey: string) {
  if (topicKey === 'CARBON') {
    activeTopicDetail.value = await getDashboardTopic('carbon') || carbonTopicDetail
  } else if (topicKey === 'MONTHLY') {
    activeTopicDetail.value = await getDashboardTopic('monthly-report') || monthlyTopicDetail
  } else {
    return
  }
  kpiFocusContext.value = null
  activeKpiKey.value = null
  lockBodyScroll()
}

function handleCloseModal() {
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
  unlockBodyScroll()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isKpiModalOpen.value) {
    handleCloseModal()
  }
}

function lockBodyScroll() {
  bodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
}

function unlockBodyScroll() {
  document.body.style.overflow = bodyOverflow
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  if (isKpiModalOpen.value) {
    unlockBodyScroll()
  }
})
</script>

<template>
  <div class="screen-wrapper">
    <div
      class="screen-canvas"
      :style="{
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }"
    >
      <div class="dashboard-page">
        <div class="dashboard-header">
          <HeaderNav />
        </div>
        <div class="dashboard-kpi">
          <TopKpiGroups @select="handleKpiSelect" />
        </div>
        <div class="dashboard-body">
          <div class="dashboard-left">
            <div class="dashboard-gis">
              <GisOverviewCesiumPanel v-if="gisConfig.useRealGisOnDashboard" @open-kpi-source="openKpiFromBusinessLink" />
              <GisOverviewPanel v-else />
            </div>
            <div class="dashboard-timeline">
              <ConstructionTimeline />
            </div>
          </div>
          <div class="dashboard-right">
            <div class="dashboard-compliance">
              <ComplianceRiskPanel />
            </div>
            <div class="dashboard-carbon" @click="handleTopicSelect('CARBON')" style="cursor: pointer;">
              <CarbonBenefitPanel />
            </div>
            <div class="dashboard-monthly" @click="handleTopicSelect('MONTHLY')" style="cursor: pointer;">
              <MonthlyReportPanel />
            </div>
          </div>
        </div>

        <Teleport to="body">
          <KpiDetailModal v-if="isKpiModalOpen && activeDetail" :detail="activeDetail" :focus-context="kpiFocusContext" @close="handleCloseModal" />
        </Teleport>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 12%, rgba(0, 174, 255, 0.05) 0%, transparent 30%),
    radial-gradient(circle at 85% 88%, rgba(166, 108, 255, 0.04) 0%, transparent 30%),
    #020b18;
}

.screen-canvas {
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  will-change: transform;
}

.dashboard-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
