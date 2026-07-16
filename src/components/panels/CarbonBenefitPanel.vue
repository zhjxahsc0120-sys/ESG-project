<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import RingChart from '@/components/charts/RingChart.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { Leaf } from 'lucide-vue-next'

const store = useDashboardStore()

const chartData = [
  { name: '施工用油', value: 58, color: '#2f9cff' },
  { name: '施工用电', value: 24, color: '#69e36f' },
  { name: '主要材料', value: 13, color: '#a66cff' },
  { name: '其他', value: 5, color: '#ffb347' },
]

const levelColors: Record<string, string> = {
  高: '#69e36f',
  较高: '#2f9cff',
  中: '#ffb347',
  低: '#8fa9c8',
}
</script>

<template>
  <PanelCard title="碳足迹与低碳增益" :icon="Leaf">
    <div class="metric-cards three">
      <div v-for="item in store.carbon" :key="item.label" class="metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value">
          {{ item.value }}
          <span v-if="item.unit" style="font-size: 11px; color: var(--text-muted);">{{ item.unit }}</span>
        </div>
        <div v-if="item.sub" style="font-size: 11px; color: var(--green); margin-top: 4px;">{{ item.sub }}</div>
      </div>
    </div>
    <div class="panel-split">
      <div class="chart-container">
        <div class="list-title" style="font-size: 13px; font-weight: 600; color: var(--text-main); margin-bottom: 6px;">
          碳足迹来源构成
        </div>
        <RingChart :data="chartData" />
      </div>
      <div class="list-card">
        <div class="list-title">主要减排措施</div>
        <div
          v-for="(item, index) in store.reductions"
          :key="index"
          class="list-item"
          style="justify-content: space-between;"
        >
          <span>{{ item.name }}</span>
          <span :style="{ color: levelColors[item.level] || '#8fa9c8', fontSize: '11px' }">
            {{ item.level }}
          </span>
        </div>
      </div>
    </div>
  </PanelCard>
</template>
