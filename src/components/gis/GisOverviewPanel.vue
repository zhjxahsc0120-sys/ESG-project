<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import RouteMapSvg from './RouteMapSvg.vue'
import GisLegend from './GisLegend.vue'
import LayerSwitch from './LayerSwitch.vue'
import SatelliteCompareCard from './SatelliteCompareCard.vue'
</script>

<template>
  <PanelCard flush>
    <div class="gis-overview-panel">
      <RouteMapSvg />
      <GisLegend />
      <LayerSwitch />
      <SatelliteCompareCard />
    </div>
  </PanelCard>
</template>
