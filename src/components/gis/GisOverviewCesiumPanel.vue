<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { gisConfig } from '@/config/gis.config'
import PanelCard from '@/components/layout/PanelCard.vue'
import { MapPinned } from 'lucide-vue-next'

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)
</script>

<template>
  <PanelCard title="GIS 地图主视觉（空间态势 + 时序影像）" :icon="MapPinned">
    <div class="dashboard-gis-cesium-panel">
      <TrafficGisOverview
        :project-id="gisConfig.projectId"
        :data-mode="gisConfig.dashboardDataMode"
        :show-legend="true"
        :show-mode-switch="true"
        :interaction-enabled="true"
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
  border-radius: 10px;
}
</style>
