<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard.store'

const store = useDashboardStore()

const props = withDefaults(defineProps<{
  activeKey?: string
}>(), {
  activeKey: 'dashboard',
})

const emit = defineEmits<{
  (event: 'navigate', key: string): void
}>()

function handleNavClick(key: string) {
  emit('navigate', key)
}
</script>

<template>
  <header class="header-nav">
    <div class="header-top-glow" />
    <div class="header-title-wrap">
      <h1 class="header-title">罗宜高速 <span>ESG</span> 综合数据管理平台</h1>
    </div>
    <nav class="header-nav-bar">
      <ul class="header-nav-list">
        <li
          v-for="item in store.navs"
          :key="item.key"
        >
          <button
            type="button"
            class="header-nav-item"
            :class="{ active: props.activeKey === item.key }"
            :data-nav-key="item.key"
            :aria-current="props.activeKey === item.key ? 'page' : undefined"
            @click="handleNavClick(item.key)"
          >
            <span class="nav-item-text">{{ item.label }}</span>
          </button>
        </li>
      </ul>
    </nav>
  </header>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.header-nav {
  height: 100%;
  display: grid;
  grid-template-rows: minmax(42px, 1.2fr) minmax(34px, 0.8fr);
  row-gap: 4px;
  position: relative;
}

.header-top-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(0, 174, 255, 0.15) 15%,
    rgba(0, 229, 255, 0.5) 50%,
    rgba(0, 174, 255, 0.15) 85%,
    transparent 100%
  );
}

.header-title-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.header-title {
  font-size: var(--fs-platform-title);
  font-weight: 700;
  letter-spacing: 0.04em;
  margin: 0;
  line-height: 1.1;
  color: var(--text-main);
  text-shadow: none;
  position: relative;
  z-index: 1;
  span { color: var(--cyan); }
}

.header-title-wrap p {
  margin: var(--space-2) 0 0;
  color: var(--text-secondary);
  font-size: var(--fs-subtitle);
  line-height: 1;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.header-nav-bar {
  height: 100%;
  width: 100%;
  padding: 0 24px;

  .header-nav-list {
    display: flex;
    justify-content: flex-start;
    gap: var(--space-6);
    list-style: none;
    margin: 0;
    padding: 0;
    height: 100%;
  }

  .header-nav-list > li {
    min-width: 160px;
    min-height: 0;
    flex-shrink: 0;
  }

  .header-nav-item {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-faint);
    border-radius: var(--radius-sm);
    background: linear-gradient(180deg, rgba(8, 31, 55, 0.88), rgba(4, 17, 33, 0.88));
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    padding: 0 8px;

    .nav-item-text {
      font-size: var(--fs-nav);
      font-weight: 500;
      color: var(--text-muted);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    &:hover {
      border-color: var(--border-blue-dim);
      background: rgba(47, 156, 255, 0.1);
      z-index: 1;
      .nav-item-text {
        color: var(--text-main);
      }
    }

    &:focus-visible {
      z-index: 3;
      outline: 2px solid var(--cyan);
      outline-offset: -2px;
    }

    &.active {
      border-color: var(--border-blue);
      background: linear-gradient(
        180deg,
        rgba(47, 156, 255, 0.32) 0%,
        rgba(10, 72, 135, 0.14) 100%
      );
      box-shadow: inset 0 0 var(--space-16) rgba(47, 156, 255, 0.12), var(--shadow-blue);
      z-index: 2;
      .nav-item-text {
        color: var(--text-main);
        font-weight: 600;
      }
      &::after {
        content: '';
        position: absolute;
        left: 50%;
        bottom: -1px;
        transform: translateX(-50%);
        width: 60%;
        height: var(--space-2);
        background: var(--cyan);
        box-shadow: 0 0 4px rgba(0, 229, 255, 0.5);
      }
    }
  }
}

@media (max-height: 900px), (max-width: 1680px) {
  .header-title { font-size: 28px; }
  .header-title-wrap p { font-size: 13px; }
  .header-nav-item { padding-inline: 5px; }
  .header-nav-item .nav-item-text { font-size: 15px; }
}
</style>
