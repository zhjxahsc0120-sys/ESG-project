<script setup lang="ts">
import type { KpiItem, KpiTheme } from '@/types/dashboard'

const props = defineProps<{
  item: KpiItem
  theme: KpiTheme
}>()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()

const themeColors: Record<KpiTheme, string> = {
  green: '#69e36f',
  blue: '#2f9cff',
  purple: '#a66cff',
}

function formatValue(value: string | number) {
  if (typeof value === 'number') {
    return value.toLocaleString('zh-CN')
  }
  return value
}

function handleClick() {
  emit('select', props.item.key)
}
</script>

<template>
  <div
    class="kpi-card" 
    :class="{ 'kpi-card--multiline': item.label.length > 10 }"
    :data-kpi-key="item.key" 
    role="button" 
    tabindex="0" 
    @click="handleClick" 
    @keydown.enter="handleClick" 
    @keydown.space.prevent="handleClick">
    <div class="kpi-label">{{ item.label }}</div>
    <div class="kpi-value-row">
      <span class="kpi-value" :style="{ color: themeColors[theme] }">
        {{ formatValue(item.value) }}
      </span>
      <span v-if="item.unit" class="kpi-unit">{{ item.unit }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.kpi-card {
  @include flex-center;
  flex-direction: column;
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 0;

  &:hover {
    border-color: var(--border-blue-dim);
    background: rgba(0, 174, 255, 0.04);
    transform: translateY(-1px);
  }

  &:focus {
    outline: none;
    border-color: var(--border-blue);
  }

  .kpi-label {
    font-size: var(--fs-caption);
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    text-align: center;
    margin-bottom: 6px;
  }

  // 长标题多行显示
  &.kpi-card--multiline .kpi-label {
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    line-height: 1.3;
    min-height: 32px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: 4px;
    justify-content: center;

    .kpi-value {
      font-family: var(--font-num);
      font-size: var(--fs-kpi-num);
      font-weight: 700;
      line-height: 1;
      text-shadow: 0 0 6px currentColor;
    }

    .kpi-unit {
      font-size: var(--fs-unit);
      color: var(--text-muted);
      font-weight: 400;
    }
  }
}
</style>
