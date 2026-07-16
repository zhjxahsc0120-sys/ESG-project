<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard.store'

const store = useDashboardStore()
</script>

<template>
  <header class="header-nav">
    <!-- 顶部光带 -->
    <div class="header-top-glow" />

    <!-- 标题 -->
    <h1 class="header-title">罗宜高速 ESG 数字化管理平台</h1>

    <!-- 导航：横向铺开 -->
    <nav class="header-nav-bar">
      <ul class="header-nav-list">
        <li
          v-for="item in store.navs"
          :key="item.key"
          class="header-nav-item"
          :class="{ active: item.active }"
        >
          <span class="nav-item-text">{{ item.label }}</span>
        </li>
      </ul>
    </nav>
  </header>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.header-nav {
  @include panel-base;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4px 16px 6px;
  position: relative;
  overflow: hidden;
}

// ── 顶部光带 ──
.header-top-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(0, 174, 255, 0.15) 15%,
    rgba(0, 229, 255, 0.5) 50%,
    rgba(0, 174, 255, 0.15) 85%,
    transparent 100%
  );
}

// ── 标题 ──
.header-title {
  font-size: var(--fs-platform-title);
  font-weight: 700;
  letter-spacing: 8px;
  margin: 0;
  line-height: 1.15;
  color: var(--text-main);
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
  background: linear-gradient(180deg, #ffffff 0%, #b0d4f5 60%, #7ab8e0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
  z-index: 1;
}

// ── 导航：横向铺开 ──
.header-nav-bar {
  margin-top: 4px;
  width: 100%;

  .header-nav-list {
    display: flex;
    gap: 0;
    list-style: none;
    margin: 0;
    padding: 0;
    justify-content: center;
  }

  .header-nav-item {
    flex: 1;
    max-width: 180px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid var(--border-faint);
    border-radius: 3px;
    background: rgba(5, 18, 38, 0.5);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    // 相邻按钮共用边框（去掉中间双线）
    margin-left: -1px;

    &:first-child {
      margin-left: 0;
      border-top-left-radius: 4px;
      border-bottom-left-radius: 4px;
    }

    &:last-child {
      border-top-right-radius: 4px;
      border-bottom-right-radius: 4px;
    }

    .nav-item-text {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-muted);
      white-space: nowrap;
    }

    &:hover {
      border-color: var(--border-blue-dim);
      background: rgba(0, 174, 255, 0.06);
      z-index: 1;

      .nav-item-text {
        color: var(--text-main);
      }
    }

    &.active {
      border-color: var(--border-blue);
      background: linear-gradient(
        180deg,
        rgba(0, 174, 255, 0.16) 0%,
        rgba(0, 174, 255, 0.04) 100%
      );
      z-index: 2;

      .nav-item-text {
        color: var(--text-main);
        font-weight: 600;
      }

      // 底部指示条
      &::after {
        content: '';
        position: absolute;
        left: 50%;
        bottom: -1px;
        transform: translateX(-50%);
        width: 60%;
        height: 2px;
        background: var(--cyan);
        box-shadow: 0 0 4px rgba(0, 229, 255, 0.5);
      }
    }
  }
}
</style>
