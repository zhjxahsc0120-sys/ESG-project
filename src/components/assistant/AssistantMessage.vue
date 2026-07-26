<script setup lang="ts">
import type { ChatMessage, AssistantDataBasis } from '@/types/assistant'

defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  (e: 'view-data-basis', data: AssistantDataBasis): void
  (e: 'follow-up', question: string): void
}>()

function getKpiColorClass(color?: string): string {
  const map: Record<string, string> = {
    green: 'kpi-green',
    blue: 'kpi-blue',
    purple: 'kpi-purple',
    orange: 'kpi-orange',
    red: 'kpi-red',
    cyan: 'kpi-cyan',
  }
  return map[color || 'blue'] || 'kpi-blue'
}

function getStatusClass(status: string): string {
  if (['整改中', '办理中', '进行中'].includes(status)) return 'st-blue'
  if (['待复查', '待处理', '临期'].includes(status)) return 'st-orange'
  if (['待销项', '逾期', '异常'].includes(status)) return 'st-red'
  if (['正常', '已完成', '已闭环'].includes(status)) return 'st-green'
  return 'st-gray'
}

function getColAlign(align?: string): string {
  return align || 'left'
}
</script>

<template>
  <div class="message-row" :class="{ 'is-user': message.role === 'user' }">
    <div v-if="message.role === 'user'" class="user-message">
      <div class="user-bubble">
        <div class="bubble-text">{{ message.content }}</div>
        <div class="bubble-time">{{ message.time }}</div>
      </div>
    </div>

    <div v-else class="assistant-message">
      <div v-if="message.loading" class="loading-bubble">
        <div class="loading-dots">
          <span /><span /><span />
        </div>
        <span class="loading-text">正在查询相关数据……</span>
      </div>

      <template v-else>
        <div class="assistant-avatar">AI</div>
        <div class="assistant-content">
          <div class="answer-summary">{{ message.content }}</div>

          <div v-if="message.kpiCards && message.kpiCards.length" class="kpi-cards">
            <div
              v-for="(card, idx) in message.kpiCards"
              :key="idx"
              class="kpi-card"
              :class="getKpiColorClass(card.color)"
            >
              <div class="kpi-label">{{ card.label }}</div>
              <div class="kpi-value">
                <span class="value-num">{{ card.value }}</span>
                <span v-if="card.unit" class="value-unit">{{ card.unit }}</span>
              </div>
            </div>
          </div>

          <div v-if="message.tableData" class="answer-table">
            <div class="table-header">
              <span class="table-title">{{ message.tableData.title }}</span>
            </div>
            <div class="table-wrap">
              <table>
                <colgroup>
                  <col
                    v-for="col in message.tableData.columns"
                    :key="col.key"
                    :style="{ width: col.width || 'auto' }"
                  />
                </colgroup>
                <thead>
                  <tr>
                    <th
                      v-for="col in message.tableData.columns"
                      :key="col.key"
                      :class="'align-' + getColAlign(col.align)"
                    >
                      {{ col.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in message.tableData.rows" :key="ri">
                    <td
                      v-for="col in message.tableData.columns"
                      :key="col.key"
                      :class="'align-' + getColAlign(col.align)"
                    >
                      <template v-if="col.key === 'handleStatus' || col.key === 'timeStatus'">
                        <span class="status-tag" :class="getStatusClass(String(row[col.key]))">
                          {{ row[col.key] }}
                        </span>
                      </template>
                      <template v-else-if="col.key === 'action'">
                        <span class="action-link">{{ row[col.key] }}</span>
                      </template>
                      <template v-else>
                        {{ row[col.key] }}
                      </template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="message.tableData.viewAllText" class="view-all-row">
              <span class="view-all-link">{{ message.tableData.viewAllText }}</span>
            </div>
          </div>

          <div v-if="message.dataBasis" class="data-basis-bar">
            <div class="basis-info">
              <span class="basis-item"><span class="basis-label">统计范围：</span>{{ message.dataBasis.scope }}</span>
              <span class="basis-item"><span class="basis-label">更新时间：</span>{{ message.dataBasis.updateTime }}</span>
              <span class="basis-item"><span class="basis-label">核验状态：</span><span class="basis-verified">已核验</span></span>
              <span class="basis-item"><span class="basis-label">数据来源：</span>施工月报、监理月报、环保检查通报</span>
            </div>
            <button class="basis-btn" @click="emit('view-data-basis', message.dataBasis!)">
              查看数据依据
            </button>
          </div>

          <div v-if="message.followUps && message.followUps.length" class="follow-ups">
            <div class="follow-title">继续查询</div>
            <div class="follow-list">
              <button
                v-for="(item, idx) in message.followUps"
                :key="idx"
                class="follow-item"
                @click="emit('follow-up', item)"
              >
                <span class="follow-icon">→</span>
                <span class="follow-text">{{ item }}</span>
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.message-row {
  display: flex;
  width: 100%;

  &.is-user {
    justify-content: flex-end;
  }
}

.user-message {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.user-bubble {
  background: linear-gradient(135deg, rgba(22, 135, 255, 0.9) 0%, rgba(37, 185, 255, 0.9) 100%);
  border-radius: 12px 12px 4px 12px;
  padding: 12px 18px;
  color: #fff;
  box-shadow: 0 4px 12px rgba(22, 135, 255, 0.25);
}

.bubble-text {
  font-size: 15px;
  line-height: 1.6;
}

.bubble-time {
  font-size: 11px;
  opacity: 0.75;
  margin-top: 6px;
  text-align: right;
}

.assistant-message {
  display: flex;
  gap: 14px;
  max-width: 100%;
}

.assistant-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.9), rgba(37, 185, 255, 0.9));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.assistant-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.answer-summary {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text-primary);
  padding: 14px 18px;
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: 4px 12px 12px 12px;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: 4px 12px 12px 12px;
}

.loading-dots {
  display: flex;
  gap: 4px;

  span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--cyan);
    animation: bounce 1.4s infinite ease-in-out both;

    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
  40% { transform: scale(1); opacity: 1; }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
}

.kpi-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.kpi-card {
  padding: 14px 16px;
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: var(--radius-sm);
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
  }

  &.kpi-green::before { background: var(--green); }
  &.kpi-blue::before { background: var(--blue); }
  &.kpi-purple::before { background: var(--purple); }
  &.kpi-orange::before { background: var(--orange); }
  &.kpi-red::before { background: var(--red); }
  &.kpi-cyan::before { background: var(--cyan); }
}

.kpi-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}

.kpi-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.value-num {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-num);
}

.kpi-green .value-num { color: var(--green); }
.kpi-blue .value-num { color: var(--cyan); }
.kpi-purple .value-num { color: var(--purple); }
.kpi-orange .value-num { color: var(--orange); }
.kpi-red .value-num { color: var(--red); }
.kpi-cyan .value-num { color: var(--cyan); }

.value-unit {
  font-size: 13px;
  color: var(--text-tertiary);
}

.answer-table {
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.table-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-soft);
}

.table-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead th {
  padding: 10px 12px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  background: rgba(4, 25, 48, 0.6);
  text-align: left;
  border-bottom: 1px solid var(--border-soft);
  white-space: nowrap;
}

tbody td {
  padding: 10px 12px;
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-faint);
  line-height: 1.4;
}

tbody tr:last-child td {
  border-bottom: none;
}

tbody tr:hover {
  background: rgba(47, 156, 255, 0.06);
}

.align-left { text-align: left; }
.align-center { text-align: center; }
.align-right { text-align: right; }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  font-size: 12px;
  border-radius: 3px;
  border: 1px solid transparent;
  white-space: nowrap;
}

.st-green {
  color: var(--green);
  border-color: rgba(67, 211, 107, 0.4);
  background: rgba(67, 211, 107, 0.1);
}

.st-blue {
  color: var(--cyan);
  border-color: rgba(37, 185, 255, 0.4);
  background: rgba(37, 185, 255, 0.1);
}

.st-orange {
  color: var(--orange);
  border-color: rgba(255, 159, 47, 0.4);
  background: rgba(255, 159, 47, 0.1);
}

.st-red {
  color: var(--red);
  border-color: rgba(255, 75, 85, 0.4);
  background: rgba(255, 75, 85, 0.1);
}

.st-gray {
  color: var(--text-tertiary);
  border-color: rgba(74, 147, 207, 0.18);
  background: rgba(8, 40, 69, 0.55);
}

.action-link {
  color: var(--cyan);
  cursor: pointer;
  font-size: 13px;

  &:hover {
    text-decoration: underline;
  }
}

.view-all-row {
  padding: 10px 16px;
  border-top: 1px solid var(--border-soft);
  text-align: center;
}

.view-all-link {
  color: var(--cyan);
  font-size: 13px;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.data-basis-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(4, 25, 48, 0.5);
  border: 1px solid rgba(74, 147, 207, 0.14);
  border-radius: var(--radius-sm);
}

.basis-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  flex: 1;
  min-width: 0;
}

.basis-item {
  font-size: 12px;
  color: var(--text-tertiary);
}

.basis-label {
  color: var(--text-muted);
}

.basis-verified {
  color: var(--green);
}

.basis-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  font-size: 13px;
  color: var(--cyan);
  background: rgba(37, 185, 255, 0.1);
  border: 1px solid rgba(37, 185, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: rgba(37, 185, 255, 0.2);
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.follow-ups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.follow-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.follow-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.follow-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  font-size: 13px;
  color: var(--text-primary);
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;

  &:hover {
    background: rgba(12, 50, 84, 0.82);
    border-color: rgba(74, 147, 207, 0.32);

    .follow-icon {
      color: var(--cyan);
      transform: translateX(3px);
    }
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.follow-icon {
  color: var(--text-tertiary);
  font-size: 14px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.follow-text {
  flex: 1;
  line-height: 1.4;
}

@media (max-width: 1600px) {
  .assistant-avatar {
    width: 36px;
    height: 36px;
    font-size: 13px;
  }

  .answer-summary {
    font-size: 14px;
    padding: 12px 16px;
  }

  .kpi-cards {
    gap: 10px;
  }

  .kpi-card {
    padding: 12px 14px;
  }

  .value-num {
    font-size: 22px;
  }

  .user-message {
    max-width: 80%;
  }
}
</style>
