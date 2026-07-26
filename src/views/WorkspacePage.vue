<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import WorkspaceNav from '@/components/workspace/WorkspaceNav.vue'
import WorkspaceHome from '@/components/workspace/WorkspaceHome.vue'
import WorkspaceTasks from '@/components/workspace/WorkspaceTasks.vue'
import WorkspaceSmartUpload from '@/components/workspace/WorkspaceSmartUpload.vue'
import WorkspaceReview from '@/components/workspace/WorkspaceReview.vue'
import WorkspaceDocuments from '@/components/workspace/WorkspaceDocuments.vue'
import TaskModal from '@/components/workspace/TaskModal.vue'
import { uploadTasks } from '@/data/workspace.mock'
import type { UploadTask } from '@/types/workspace'

const route = useRoute()
const router = useRouter()

const activeNav = ref('workspace')
const selectedStatus = ref('')
const selectedTaskId = ref<string | null>(null)
const forceTab = ref<string>('')

// 从 URL query ?t= 同步初始 Tab
function syncTabFromQuery() {
  const t = route.query.t as string | undefined
  if (t && ['workspace', 'tasks', 'smart-upload', 'review', 'documents'].includes(t)) {
    activeNav.value = t
  }
}

syncTabFromQuery()

const currentTask = computed(() => {
  if (!selectedTaskId.value) return null
  return uploadTasks.find(t => t.id === selectedTaskId.value) || {
    id: selectedTaskId.value,
    name: '任务办理',
    module: 'E',
    moduleName: '环境环保',
    deadline: '',
    deadlineDisplay: '',
    progressCurrent: 0,
    progressTotal: 1,
    status: '待上传',
    nextStep: '开始办理',
  } as UploadTask
})

function handleNavigate(key: string, status?: string) {
  activeNav.value = key
  if (status) {
    selectedStatus.value = status
  } else {
    selectedStatus.value = ''
  }
  // 同步 ?t= 深链
  router.replace({ query: { t: key } })
}

function handleOpenTask(taskId: string, tab?: string) {
  selectedTaskId.value = taskId
  forceTab.value = tab || ''
}

function handleCloseModal() {
  selectedTaskId.value = null
  forceTab.value = ''
}

function handlePlatformNav(key: string) {
  if (key === 'dashboard') {
    router.push('/')
  } else if (key === 'assistant') {
    router.push('/assistant')
  } else if (key === 'workspace') {
    // already here
  }
}

watch(() => route.query.t, () => {
  syncTabFromQuery()
})
</script>

<template>
  <div class="workspace-page">
    <!-- 平台统一 HeaderNav（80px） -->
    <div class="workspace-header-nav">
      <HeaderNav active-key="workspace" @navigate="handlePlatformNav" />
    </div>

    <!-- 二级 Tab -->
    <WorkspaceNav :active-nav="activeNav" @navigate="handleNavigate" />

    <main class="workspace-main">
      <WorkspaceHome
        v-if="activeNav === 'workspace'"
        @navigate="handleNavigate"
        @open-task="handleOpenTask"
      />
      <WorkspaceTasks
        v-else-if="activeNav === 'tasks'"
        :initial-status="selectedStatus"
        @open-task="handleOpenTask"
      />
      <WorkspaceSmartUpload
        v-else-if="activeNav === 'smart-upload'"
      />
      <WorkspaceReview
        v-else-if="activeNav === 'review'"
        @open-task="handleOpenTask"
      />
      <WorkspaceDocuments
        v-else-if="activeNav === 'documents'"
      />
    </main>

    <TaskModal
      v-if="currentTask"
      :task="currentTask"
      :force-tab="forceTab"
      @close="handleCloseModal"
    />
  </div>
</template>

<style scoped>
.workspace-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: linear-gradient(180deg, #020b18 0%, #051a32 100%);
}

.workspace-header-nav {
  height: var(--dashboard-header-h, 80px);
  flex: 0 0 var(--dashboard-header-h, 80px);
}

.workspace-main {
  flex: 1;
  overflow: hidden;
}
</style>