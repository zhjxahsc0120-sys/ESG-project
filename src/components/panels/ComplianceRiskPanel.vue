<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import BarMetricChart from '@/components/charts/BarMetricChart.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { ShieldCheck } from 'lucide-vue-next'

const store = useDashboardStore()
</script>

<template>
  <PanelCard title="合规保障与风险防控成效" :icon="ShieldCheck">
    <div class="metric-cards">
      <div v-for="item in store.compliance" :key="item.label" class="metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value">{{ item.value }} {{ item.unit }}</div>
      </div>
    </div>
    <div class="panel-split">
      <div class="chart-container">
        <div class="list-title" style="font-size: 13px; font-weight: 600; color: var(--text-main); margin-bottom: 6px;">
          成效构成
        </div>
        <BarMetricChart :data="store.effectiveness" />
      </div>
      <div class="list-card">
        <div class="list-title">重点保障事项</div>
        <div v-for="(item, index) in store.safeguards" :key="index" class="list-item">
          {{ item }}
        </div>
      </div>
    </div>
  </PanelCard>
</template>
