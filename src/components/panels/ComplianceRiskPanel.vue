<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import BarMetricChart from '@/components/charts/BarMetricChart.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { ShieldCheck } from 'lucide-vue-next'

const store = useDashboardStore()

function splitSafeguard(item: string) {
  const separatorIndex = item.indexOf('，')

  if (separatorIndex === -1) {
    return { title: item, detail: '' }
  }

  return {
    title: item.slice(0, separatorIndex),
    detail: item.slice(separatorIndex + 1),
  }
}
</script>

<template>
  <PanelCard title="合规保障与风险防控成效" :icon="ShieldCheck">
    <div class="compliance-grid">
      <div v-for="item in store.compliance" :key="item.label" class="metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value">{{ item.value }} {{ item.unit }}</div>
      </div>
      <div class="compliance-subpanel effectiveness-card">
        <div class="compliance-subtitle">
          成效构成
        </div>
        <BarMetricChart :data="store.effectiveness" />
      </div>
      <div class="compliance-subpanel safeguard-card">
        <div class="compliance-subtitle">重点保障事项</div>
        <div class="safeguard-list">
          <div v-for="(item, index) in store.safeguards" :key="index" class="safeguard-item">
            <span class="safeguard-dot" />
            <span class="safeguard-content">
              <span class="safeguard-title">{{ splitSafeguard(item).title }}</span>
              <span v-if="splitSafeguard(item).detail" class="safeguard-detail">
                {{ splitSafeguard(item).detail }}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </PanelCard>
</template>

<style scoped lang="scss">
.compliance-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-width: 0;
  min-height: 0;
}

.compliance-grid > .metric-card {
  min-width: 0;
}

.compliance-subpanel {
  min-width: 0;
  min-height: 0;
  height: 100%;
  padding: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-blue-dim);
  border-radius: 6px;
  overflow: hidden;
}

.effectiveness-card,
.safeguard-card {
  display: flex;
  flex-direction: column;
}

.effectiveness-card {
  grid-column: 1 / span 2;
}

.safeguard-card {
  grid-column: 3 / span 2;
}

.compliance-subtitle {
  height: 22px;
  margin: 0 0 4px;
  color: #fff;
  font-size: 15px;
  font-weight: 650;
  line-height: 22px;
  flex-shrink: 0;
}

.effectiveness-card :deep(.bar-metric-list) {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
}

.safeguard-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.safeguard-item {
  display: grid;
  grid-template-columns: 5px minmax(0, 1fr);
  align-items: start;
  column-gap: 6px;
  min-width: 0;
}

.safeguard-dot {
  width: 4px;
  height: 4px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--cyan);
}

.safeguard-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.safeguard-title,
.safeguard-detail {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.safeguard-title {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  line-height: 17px;
}

.safeguard-detail {
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 400;
  line-height: 15px;
}
</style>
