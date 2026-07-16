<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard.store'
import KpiGroupPanel from './KpiGroupPanel.vue'

const store = useDashboardStore()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()

function handleSelect(key: string) {
  emit('select', key)
}
</script>

<template>
  <div class="kpi-groups">
    <KpiGroupPanel v-for="group in store.kpis" :key="group.key" :group="group" @select="handleSelect" />
  </div>
</template>
