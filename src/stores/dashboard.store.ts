import { defineStore } from 'pinia'
import { ref, onMounted } from 'vue'
import type {
  NavItem,
  KpiGroup,
  RoutePoint,
  RouteSegment,
  SensitiveArea,
  ComplianceMetric,
  EffectivenessItem,
  WarningListItem,
  CarbonSource,
  ReductionMeasure,
  MonthlyReport,
  TimelineStep,
} from '@/types/dashboard'
import type { MonthlyReadiness } from '@/types/monthly-report'
import {
  navItems,
  kpiGroups,
  routePoints,
  routeSegments,
  sensitiveAreas,
  complianceMetrics,
  effectivenessItems,
  safeguardItems,
  warningListItems,
  carbonMetrics,
  carbonSources,
  reductionMeasures,
  monthlyReport,
  timelineSteps,
} from '@/data/dashboard.mock'
import { createMonthlyReadinessMock } from '@/data/monthly-readiness.mock'
import { getDashboardKpis, getDashboardPanels, getMonthlyReportReadiness } from '@/services/api'
import { validateMonthlyReadiness } from '@/utils/monthly-readiness'

export const useDashboardStore = defineStore('dashboard', () => {
  const navs = ref<NavItem[]>(navItems)
  const kpis = ref<KpiGroup[]>(kpiGroups)
  const points = ref<RoutePoint[]>(routePoints)
  const segments = ref<RouteSegment[]>(routeSegments)
  const areas = ref<SensitiveArea[]>(sensitiveAreas)
  const compliance = ref<ComplianceMetric[]>(complianceMetrics)
  const effectiveness = ref<EffectivenessItem[]>(effectivenessItems)
  const safeguards = ref<string[]>(safeguardItems)
  const warningItems = ref<WarningListItem[]>(warningListItems)
  const carbon = ref(carbonMetrics)
  const carbonSrc = ref<CarbonSource[]>(carbonSources)
  const reductions = ref<ReductionMeasure[]>(reductionMeasures)
  const monthly = ref<MonthlyReport>(monthlyReport)
  const monthlyReadiness = ref<MonthlyReadiness>(createMonthlyReadinessMock())
  const monthlyReadinessError = ref<string | null>(null)
  const timeline = ref<TimelineStep[]>(timelineSteps)

  const activeLayers = ref<string[]>(['all', 'environment', 'risk'])

  async function loadKpis() {
    const data = await getDashboardKpis()
    if (data && data.groups && data.groups.length > 0) {
      kpis.value = data.groups as KpiGroup[]
    }
  }

  async function loadPanels() {
    const data = await getDashboardPanels()
    if (!data) return
    if (data.compliance?.metrics) compliance.value = data.compliance.metrics as ComplianceMetric[]
    if (data.compliance?.effectiveness) effectiveness.value = data.compliance.effectiveness as EffectivenessItem[]
    if (data.compliance?.safeguards) safeguards.value = data.compliance.safeguards
    if (data.compliance?.warningItems) warningItems.value = data.compliance.warningItems as WarningListItem[]
    if (data.carbon?.metrics) carbon.value = data.carbon.metrics as typeof carbonMetrics
    if (data.carbon?.sources) carbonSrc.value = data.carbon.sources as CarbonSource[]
    if (data.carbon?.reductions) reductions.value = data.carbon.reductions as ReductionMeasure[]
    if (data.monthly) monthly.value = data.monthly as MonthlyReport
    if (data.timeline) timeline.value = data.timeline as TimelineStep[]
    if (data.gis?.routePoints) points.value = data.gis.routePoints as RoutePoint[]
    if (data.gis?.routeSegments) segments.value = data.gis.routeSegments as RouteSegment[]
    if (data.gis?.sensitiveAreas) areas.value = data.gis.sensitiveAreas as SensitiveArea[]
  }

  async function loadMonthlyReadiness(reportPeriod = '2026-07') {
    try {
      const data = await getMonthlyReportReadiness(reportPeriod)
      if (!data) {
        throw new Error(`月报资料归集率接口请求失败：${reportPeriod}`)
      }

      const validationErrors = validateMonthlyReadiness(data)
      if (validationErrors.length > 0) {
        throw new Error(`月报资料归集率数据校验失败：${validationErrors.join('；')}`)
      }

      monthlyReadiness.value = data
      monthlyReadinessError.value = null
    } catch (error) {
      monthlyReadiness.value = createMonthlyReadinessMock()
      monthlyReadinessError.value = error instanceof Error ? error.message : String(error)
      if (import.meta.env.DEV) {
        console.warn('[monthly-readiness]', monthlyReadinessError.value)
      }
    }
  }

  function toggleLayer(layer: string) {
    const idx = activeLayers.value.indexOf(layer)
    if (idx > -1) {
      activeLayers.value.splice(idx, 1)
    } else {
      activeLayers.value.push(layer)
    }
  }

  loadKpis()
  loadPanels()
  void loadMonthlyReadiness()

  return {
    navs,
    kpis,
    points,
    segments,
    areas,
    compliance,
    effectiveness,
    safeguards,
    warningItems,
    carbon,
    carbonSrc,
    reductions,
    monthly,
    monthlyReadiness,
    monthlyReadinessError,
    timeline,
    activeLayers,
    toggleLayer,
    loadKpis,
    loadPanels,
    loadMonthlyReadiness,
  }
})
