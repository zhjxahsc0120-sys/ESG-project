<script setup lang="ts">
import { ref } from 'vue'
import { Bell, User } from 'lucide-vue-next'

defineProps<{
  activeNav: string
}>()

const emit = defineEmits<{
  (e: 'navigate', name: string): void
}>()

const navItems = [
  { key: 'workspace', label: '工作台首页' },
  { key: 'tasks', label: '我的上传任务' },
  { key: 'smart-upload', label: 'ESG智能入库' },
  { key: 'review', label: '审核管理' },
  { key: 'documents', label: '资料中心与档案' },
]

function handleNavClick(key: string) {
  emit('navigate', key)
}
</script>

<template>
  <header class="workspace-header">
    <div class="header-left">
      <div class="logo">
        <div class="logo-icon">ESG</div>
      </div>
      <div class="platform-title">罗宜高速 ESG 数字化管理平台｜数据填报与上传工作台</div>
    </div>
    <div class="header-right">
      <div class="notification-bell">
        <Bell :size="20" />
        <span class="badge">8</span>
      </div>
      <div class="user-info">
        <div class="user-avatar">
          <User :size="18" />
        </div>
        <span class="user-name">项目管理员</span>
      </div>
    </div>
  </header>

  <nav class="workspace-nav">
    <button
      v-for="item in navItems"
      :key="item.key"
      :class="['nav-item', { active: activeNav === item.key }]"
      @click="handleNavClick(item.key)"
    >
      {{ item.label }}
    </button>
  </nav>
</template>

<style scoped>
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, #031020 0%, #051a32 100%);
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  font-size: 14px;
  font-weight: 700;
  color: #031020;
}

.platform-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8f3ff;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.notification-bell {
  position: relative;
  cursor: pointer;
  color: #8fa9c8;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.notification-bell:hover {
  background: rgba(105, 227, 111, 0.1);
  color: #69e36f;
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  background: #ff4f5e;
  color: white;
  font-size: 10px;
  font-weight: 700;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba(105, 227, 111, 0.08);
  border-radius: 20px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #031020;
}

.user-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
}

.workspace-nav {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  padding: 0 24px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.nav-item {
  flex: 1;
  max-width: 180px;
  padding: 14px 12px;
  border: none;
  background: transparent;
  color: #8fa9c8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  text-align: center;
}

.nav-item:hover {
  color: #e8f3ff;
  background: rgba(105, 227, 111, 0.05);
}

.nav-item.active {
  color: #69e36f;
  border-bottom-color: #69e36f;
  background: rgba(105, 227, 111, 0.08);
}
</style>
