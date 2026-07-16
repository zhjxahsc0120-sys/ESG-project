<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)
</script>

<template>
  <section class="gis-preview-container">
    <TrafficGisOverview
      project-id="LUOYI-ESG"
      data-mode="api"
      :show-legend="true"
      :show-mode-switch="true"
    />
  </section>
</template>

<style scoped>
.gis-preview-container {
  position: relative;
  width: 100%;
  height: 720px;
  min-height: 520px;
}
</style>
