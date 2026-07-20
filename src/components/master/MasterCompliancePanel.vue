<script setup lang="ts">
import { ShieldCheck } from 'lucide-vue-next'
import {
  complianceMetrics,
  complianceBars,
  complianceFocus,
} from '@/data/master.mock'

const statusColor: Record<string, string> = {
  normal: 'var(--green)',
  warning: 'var(--orange)',
  danger: 'var(--red)',
}
</script>

<template>
  <div class="master-panel compliance-panel">
    <div class="panel-header">
      <ShieldCheck :size="16" style="color: var(--green)" />
      <span class="panel-title">合规保障与风险防控成效</span>
    </div>
    <div class="panel-body">
      <!-- 顶部 4 张度量卡 -->
      <div class="metric-cards">
        <div v-for="m in complianceMetrics" :key="m.key" class="metric-card">
          <div class="metric-value-row">
            <span class="metric-value">{{ m.value }}</span>
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <span class="metric-label">{{ m.label }}</span>
        </div>
      </div>
      <!-- 下部左右两区 -->
      <div class="compliance-lower">
        <!-- 左：成效构成 -->
        <div class="compliance-left">
          <div class="sub-title">成效构成</div>
          <div class="bar-list">
            <div v-for="(b, i) in complianceBars" :key="i" class="bar-row">
              <div class="bar-info">
                <span class="bar-name">{{ b.name }}</span>
                <span class="bar-val">{{ b.value }} {{ b.unit }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: b.ratio + '%' }" />
              </div>
            </div>
          </div>
        </div>
        <!-- 右：重点保障事项 -->
        <div class="compliance-right">
          <div class="sub-title">重点保障事项</div>
          <div class="focus-list">
            <div
              v-for="(f, i) in complianceFocus"
              :key="i"
              class="focus-item"
            >
              <span class="focus-dot" :style="{ background: statusColor[f.status] }" />
              <span class="focus-title">{{ f.title }}</span>
              <span class="focus-status" :style="{ color: statusColor[f.status] }">{{ f.statusLabel }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
