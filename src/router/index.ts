import { createRouter, createWebHashHistory } from 'vue-router'
import DashboardPage from '@/views/DashboardPage.vue'
import WorkspacePage from '@/views/WorkspacePage.vue'
import GisPreviewPage from '@/views/GisPreviewPage.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardPage,
  },
  {
    path: '/workspace',
    name: 'workspace',
    component: WorkspacePage,
  },
  {
    path: '/gis-preview',
    name: 'gis-preview',
    component: GisPreviewPage,
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router
