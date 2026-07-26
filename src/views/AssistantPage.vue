<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import AssistantSidebar from '@/components/assistant/AssistantSidebar.vue'
import AssistantChatArea from '@/components/assistant/AssistantChatArea.vue'
import AssistantDataDrawer from '@/components/assistant/AssistantDataDrawer.vue'
import type { ChatMessage, AssistantDataBasis } from '@/types/assistant'
import {
  recentSessions,
  quickCategories,
  welcomeQuestions,
  createEnvIssuesAnswer,
  getEmptyAcceptanceSession,
} from '@/data/assistant.mock'

const SCREEN_WIDTH = 1920
const SCREEN_HEIGHT = 1080

const route = useRoute()
const router = useRouter()

const windowWidth = ref(SCREEN_WIDTH)
const windowHeight = ref(SCREEN_HEIGHT)

const scale = computed(() => {
  const scaleX = windowWidth.value / SCREEN_WIDTH
  const scaleY = windowHeight.value / SCREEN_HEIGHT
  return Math.min(scaleX, scaleY)
})

const translateX = computed(() => {
  const scaledWidth = SCREEN_WIDTH * scale.value
  return (windowWidth.value - scaledWidth) / 2
})

const translateY = computed(() => {
  const scaledHeight = SCREEN_HEIGHT * scale.value
  return (windowHeight.value - scaledHeight) / 2
})

const isAcceptanceMode = computed(() => route.query.acceptance === '1')

const messages = ref<ChatMessage[]>([])
const drawerOpen = ref(false)
const drawerData = ref<AssistantDataBasis | null>(null)
const isLoading = ref(false)

function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

function handleNavClick(key: string) {
  if (key === 'dashboard') {
    router.push('/')
  } else if (key === 'assistant') {
    // already here
  } else if (key === 'workspace') {
    router.push('/workspace')
  }
}

function handleSendMessage(text: string) {
  if (!text.trim() || isLoading.value) return
  const userMsg: ChatMessage = {
    id: 'u' + Date.now(),
    role: 'user',
    content: text,
    time: formatNow(),
  }
  messages.value.push(userMsg)
  isLoading.value = true
  const loadingMsg: ChatMessage = {
    id: 'a' + Date.now(),
    role: 'assistant',
    content: '',
    time: formatNow(),
    loading: true,
  }
  messages.value.push(loadingMsg)
  setTimeout(() => {
    const answer = createEnvIssuesAnswer()
    answer.id = 'a' + Date.now()
    const lastIdx = messages.value.length - 1
    if (messages.value[lastIdx]?.loading) {
      messages.value[lastIdx] = answer
    } else {
      messages.value.push(answer)
    }
    isLoading.value = false
  }, 1200)
}

function formatNow(): string {
  if (isAcceptanceMode.value) return '2026-07-20 10:30:00'
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function handleNewSession() {
  messages.value = []
  isLoading.value = false
}

function handleWelcomeClick(question: string) {
  handleSendMessage(question)
}

function handleQuickCategory(question: string) {
  handleSendMessage(question)
}

function handleSessionClick(sessionId: string) {
  if (isAcceptanceMode.value && sessionId === '1') {
    messages.value = getEmptyAcceptanceSession()
  }
}

function handleViewDataBasis(data: AssistantDataBasis) {
  drawerData.value = data
  drawerOpen.value = true
}

function handleFollowUp(question: string) {
  handleSendMessage(question)
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  if (isAcceptanceMode.value) {
    messages.value = getEmptyAcceptanceSession()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="screen-wrapper">
    <div
      class="screen-canvas"
      :style="{
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }"
    >
      <div class="assistant-page">
        <div class="assistant-header">
          <HeaderNav active-key="assistant" @navigate="handleNavClick" />
        </div>
        <div class="assistant-body">
          <AssistantSidebar
            :sessions="recentSessions"
            :categories="quickCategories"
            @new-session="handleNewSession"
            @session-click="handleSessionClick"
            @category-click="handleQuickCategory"
          />
          <AssistantChatArea
            :messages="messages"
            :welcome-questions="welcomeQuestions"
            :is-loading="isLoading"
            :is-acceptance="isAcceptanceMode"
            @send="handleSendMessage"
            @welcome-click="handleWelcomeClick"
            @view-data-basis="handleViewDataBasis"
            @follow-up="handleFollowUp"
          />
        </div>

        <Teleport to="body">
          <AssistantDataDrawer
            v-if="drawerOpen && drawerData"
            :data="drawerData"
            :scale="scale"
            @close="drawerOpen = false"
          />
        </Teleport>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.screen-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #020b18;
}

.screen-canvas {
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  will-change: transform;
}

.assistant-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: var(--main-gap);
  gap: var(--main-gap);
  position: relative;
  background: linear-gradient(180deg, #030d18 0%, #06182a 42%, #041322 100%);
  overflow: hidden;

  // 第二层：极淡网格纹理
  &::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image:
      linear-gradient(rgba(62, 145, 214, 0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(62, 145, 214, 0.035) 1px, transparent 1px);
    background-size: 56px 56px;
    z-index: 0;
  }

  // 第三层：中部柔和光晕
  &::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(
        circle at 58% 38%,
        rgba(30, 126, 214, 0.10) 0%,
        rgba(30, 126, 214, 0.045) 28%,
        transparent 58%
      );
    z-index: 0;
  }
}

.assistant-header {
  position: relative;
  z-index: 1;
  height: var(--dashboard-header-h);
  flex-shrink: 0;
}

.assistant-body {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  gap: var(--main-gap);
  min-height: 0;
}
</style>
