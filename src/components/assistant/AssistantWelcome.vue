<script setup lang="ts">
defineProps<{
  questions: string[]
}>()

const emit = defineEmits<{
  (e: 'question-click', question: string): void
}>()

const categories = [
  'ESG指标',
  '环保、安全、治理事项',
  '碳排放及低碳措施',
  '月报准备情况',
  '平台资料档案',
]
</script>

<template>
  <div class="welcome-area">
    <div class="welcome-content">
      <h2 class="welcome-title">今天需要查询什么？</h2>
      <p class="welcome-desc">您可以查询：</p>
      <div class="welcome-categories">
        <span v-for="(cat, idx) in categories" :key="idx" class="cat-tag">{{ cat }}</span>
      </div>

      <div class="suggestions">
        <div class="suggestions-title">推荐问题</div>
        <div class="suggestion-list">
          <div
            v-for="(q, idx) in questions"
            :key="idx"
            class="suggestion-item"
            @click="emit('question-click', q)"
          >
            <span class="suggestion-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </span>
            <span class="suggestion-text">{{ q }}</span>
            <span class="suggestion-arrow">→</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.welcome-area {
  width: 100%;
  padding-top: 12px;
}

.welcome-content {
  max-width: 780px;
  margin: 0 auto;
  text-align: left;
}

.welcome-title {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.welcome-desc {
  margin: 0 0 12px;
  font-size: 14px;
  color: var(--text-tertiary);
}

.welcome-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 32px;
}

.cat-tag {
  padding: 4px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: rgba(8, 40, 69, 0.55);
  border: 1px solid rgba(74, 147, 207, 0.14);
  border-radius: 12px;
}

.suggestions-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(74, 147, 207, 0.18);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(12, 50, 84, 0.82);
    border-color: rgba(74, 147, 207, 0.32);

    .suggestion-arrow {
      transform: translateX(4px);
      color: var(--cyan);
    }
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.suggestion-icon {
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  svg {
    width: 18px;
    height: 18px;
  }
}

.suggestion-text {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.4;
}

.suggestion-arrow {
  color: var(--text-tertiary);
  font-size: 14px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

@media (max-width: 1600px) {
  .welcome-title {
    font-size: 26px;
  }

  .welcome-categories {
    margin-bottom: 24px;
  }

  .suggestion-item {
    padding: 14px 16px;
  }
}
</style>
