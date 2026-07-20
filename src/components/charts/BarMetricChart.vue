<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: { label: string; value: number }[]
}>()

const maxValue = computed(() => Math.max(...props.data.map((item) => item.value), 1))

function progressWidth(value: number) {
  return `${(value / maxValue.value) * 100}%`
}
</script>

<template>
  <div class="bar-metric-list">
    <div v-for="item in data" :key="item.label" class="bar-metric-row">
      <span class="bar-metric-name">{{ item.label }}</span>
      <span class="bar-metric-track">
        <span class="bar-metric-fill" :style="{ width: progressWidth(item.value) }" />
      </span>
      <span class="bar-metric-value">{{ item.value }}项</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
.bar-metric-list {
  flex: 1;
  display: grid;
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 4px;
  width: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.bar-metric-row {
  display: grid;
  grid-template-columns: 110px minmax(0, 1fr) 34px;
  align-items: center;
  column-gap: 6px;
  min-width: 0;
  min-height: 0;
}

.bar-metric-name,
.bar-metric-value {
  font-size: 12px;
  line-height: 16px;
  white-space: nowrap;
}

.bar-metric-name {
  color: var(--text-muted);
  text-align: left;
}

.bar-metric-value {
  color: var(--text-main);
  font-weight: 600;
  text-align: right;
}

.bar-metric-track {
  display: block;
  width: 100%;
  height: 7px;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(47, 156, 255, 0.12);
}

.bar-metric-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(47, 156, 255, 0.35), #2f9cff);
}
</style>
