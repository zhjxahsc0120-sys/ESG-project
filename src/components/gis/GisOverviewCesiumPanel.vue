<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { gisConfig } from '@/config/gis.config'
import PanelCard from '@/components/layout/PanelCard.vue'
import type { GisBusinessLinkOpenPayload } from '@/modules/traffic-gis-overview/types'

const emit = defineEmits<{
  openKpiSource: [payload: GisBusinessLinkOpenPayload]
}>()

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)
</script>

<template>
  <PanelCard flush>
    <div class="dashboard-gis-cesium-panel">
      <TrafficGisOverview
        :project-id="gisConfig.projectId"
        :data-mode="gisConfig.dashboardDataMode"
        :show-legend="true"
        :show-mode-switch="true"
        :show-config-button="false"
        :interaction-enabled="true"
        presentation-mode="dashboard"
        @open-kpi-source="(payload) => emit('openKpiSource', payload)"
      />
    </div>
  </PanelCard>
</template>

<style scoped>
.dashboard-gis-cesium-panel {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}
</style>
