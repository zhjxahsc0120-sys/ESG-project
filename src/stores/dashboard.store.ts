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
  CarbonSource,
  ReductionMeasure,
  MonthlyReport,
  TimelineStep,
} from '@/types/dashboard'
import {
  navItems,
  kpiGroups,
  routePoints,
  routeSegments,
  sensitiveAreas,
  complianceMetrics,
  effectivenessItems,
  safeguardItems,
  carbonMetrics,
  carbonSources,
  reductionMeasures,
  monthlyReport,
  timelineSteps,
} from '@/data/dashboard.mock'
import { getDashboardKpis, getDashboardPanels } from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  const navs = ref<NavItem[]>(navItems)
  const kpis = ref<KpiGroup[]>(kpiGroups)
  const points = ref<RoutePoint[]>(routePoints)
  const segments = ref<RouteSegment[]>(routeSegments)
  const areas = ref<SensitiveArea[]>(sensitiveAreas)
  const compliance = ref<ComplianceMetric[]>(complianceMetrics)
  const effectiveness = ref<EffectivenessItem[]>(effectivenessItems)
  const safeguards = ref<string[]>(safeguardItems)
  const carbon = ref(carbonMetrics)
  const carbonSrc = ref<CarbonSource[]>(carbonSources)
  const reductions = ref<ReductionMeasure[]>(reductionMeasures)
  const monthly = ref<MonthlyReport>(monthlyReport)
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
    if (data.carbon?.metrics) carbon.value = data.carbon.metrics as typeof carbonMetrics
    if (data.carbon?.sources) carbonSrc.value = data.carbon.sources as CarbonSource[]
    if (data.carbon?.reductions) reductions.value = data.carbon.reductions as ReductionMeasure[]
    if (data.monthly) monthly.value = data.monthly as MonthlyReport
    if (data.timeline) timeline.value = data.timeline as TimelineStep[]
    if (data.gis?.routePoints) points.value = data.gis.routePoints as RoutePoint[]
    if (data.gis?.routeSegments) segments.value = data.gis.routeSegments as RouteSegment[]
    if (data.gis?.sensitiveAreas) areas.value = data.gis.sensitiveAreas as SensitiveArea[]
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

  return {
    navs,
    kpis,
    points,
    segments,
    areas,
    compliance,
    effectiveness,
    safeguards,
    carbon,
    carbonSrc,
    reductions,
    monthly,
    timeline,
    activeLayers,
    toggleLayer,
    loadKpis,
    loadPanels,
  }
})
