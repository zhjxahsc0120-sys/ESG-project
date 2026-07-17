<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import ProgressRing from '@/components/charts/ProgressRing.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { FileText, Activity, CheckCircle } from 'lucide-vue-next'

const store = useDashboardStore()
</script>

<template>
  <PanelCard title="月报准备与输出" :icon="FileText">
    <div class="monthly-report-panel">
      <div class="progress-section">
        <div class="progress-label">{{ store.monthly.month }}</div>
        <ProgressRing :progress="store.monthly.progress" />
        <div class="progress-sub">
          待补资料 {{ store.monthly.pendingCount }} 项，待确认 {{ store.monthly.confirmCount }} 项
        </div>
        <div class="status-blocks">
          <div class="status-block">
            <Activity class="status-icon" />
            <span>当前状态：{{ store.monthly.currentStatus || '报告编制' }}</span>
          </div>
          <div class="status-block">
            <CheckCircle class="status-icon" />
            <span>预计完成 {{ store.monthly.expectedCompletion || '7月12日' }}</span>
          </div>
        </div>
      </div>
      <div class="materials-section">
        <div class="materials-title">待补资料清单</div>
        <table class="materials-table">
          <thead>
            <tr>
              <th>资料名称</th>
              <th>责任单位</th>
              <th>截止日期</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in store.monthly.materials" :key="item.name">
              <td>{{ item.name }}</td>
              <td>{{ item.owner }}</td>
              <td>{{ item.deadline }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </PanelCard>
</template>
