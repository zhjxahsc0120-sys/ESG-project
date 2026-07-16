<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, FileText, Download, Eye, Link2, Tag, Clock, User, Folder } from 'lucide-vue-next'
import { documentStatusCards as mockDocumentStatusCards, documentCategories, documentTypes, documents as mockDocuments } from '@/data/workspace.mock'
import { getDocumentsSummary, getDocuments, getDocumentDetail, getDocumentVersions, getDocumentRelations } from '@/services/api'
import type { StatusCard, Document as DocumentType } from '@/types/workspace'
import type { DocumentVersionApi } from '@/services/api'
import { onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const selectedCategory = ref('全部资料')
const selectedType = ref('')
const searchKeyword = ref('')
const selectedCycle = ref('')
const selectedSource = ref('')
const selectedStatus = ref('')
const documentList = ref<DocumentType[]>([...mockDocuments])
const statusCards = ref<StatusCard[]>([...mockDocumentStatusCards])
const selectedDoc = ref<DocumentType>({ ...mockDocuments[0] })
const documentVersions = ref<DocumentVersionApi[]>([])
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.scopes.includes('documents')) {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const [summaryRes, docsRes] = await Promise.all([
    getDocumentsSummary(),
    getDocuments(),
  ])
  
  if (summaryRes) {
    statusCards.value = [
      { label: '资料总数', value: summaryRes.documentTotal, unit: '份', color: '#69e36f' },
      { label: '本月新增', value: summaryRes.monthNew, unit: '份', color: '#2f9cff' },
      { label: '待归档', value: summaryRes.pendingArchive, unit: '份', color: '#ffb347' },
      { label: '即将失效', value: summaryRes.expiringSoon, unit: '份', color: '#ff4f5e' },
    ]
  }
  
  if (docsRes && docsRes.items && docsRes.items.length > 0) {
    documentList.value = docsRes.items.map(item => ({
      id: item.id,
      name: item.documentName,
      type: item.documentType,
      module: item.module,
      cycle: item.period,
      version: item.version,
      source: item.source,
      relatedTaskCount: item.relationCount,
      status: item.validityStatus as '有效' | '即将失效' | '已失效',
      uploadTime: item.uploadedAt,
    }))
  }
}

function showMessage(message: string, type: 'info' | 'success' | 'error' = 'info') {
  pageMessage.value = message
  pageMessageType.value = type
}

const categoryLabelToModule: Record<string, string> = {
  '环境环保': 'E',
  '社会责任': 'S',
  '治理合规': 'G',
}

const filteredDocuments = computed(() => {
  return documentList.value.filter(doc => {
    if (selectedCategory.value !== '全部资料') {
      const module = categoryLabelToModule[selectedCategory.value]
      if (module && doc.module !== module) return false
    }
    if (selectedType.value && doc.type !== selectedType.value) return false
    if (searchKeyword.value && !doc.name.includes(searchKeyword.value)) return false
    if (selectedCycle.value && doc.cycle !== selectedCycle.value) return false
    if (selectedSource.value && doc.source !== selectedSource.value) return false
    if (selectedStatus.value && doc.status !== selectedStatus.value) return false
    return true
  })
})

const computedCategories = computed(() => {
  const total = documentList.value.length
  const counts: Record<string, number> = { E: 0, S: 0, G: 0 }
  for (const doc of documentList.value) {
    if (doc.module === 'E' || doc.module === 'S' || doc.module === 'G') {
      counts[doc.module]++
    }
  }
  return [
    { label: '全部资料', value: total },
    { label: '环境环保', value: counts.E },
    { label: '社会责任', value: counts.S },
    { label: '治理合规', value: counts.G },
  ]
})

const computedTypes = computed(() => {
  const map = new Map<string, number>()
  for (const doc of documentList.value) {
    map.set(doc.type, (map.get(doc.type) || 0) + 1)
  }
  return Array.from(map.entries()).map(([label, value]) => ({ label, value }))
})

function getModuleColor(module: string) {
  switch (module) {
    case 'E': return '#69e36f'
    case 'S': return '#2f9cff'
    case 'G': return '#a66cff'
    default: return '#8fa9c8'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case '有效': return '#69e36f'
    case '即将失效': return '#ffb347'
    case '已失效': return '#ff4f5e'
    default: return '#8fa9c8'
  }
}

function handleReset() {
  searchKeyword.value = ''
  selectedCycle.value = ''
  selectedSource.value = ''
  selectedStatus.value = ''
}

async function handleSelectDocument(doc: DocumentType) {
  selectedDoc.value = { ...doc }
  await loadDocumentDetail(doc.id)
}

async function loadDocumentDetail(documentId: string | number) {
  const [detailRes, versionsRes, relationsRes] = await Promise.all([
    getDocumentDetail(documentId),
    getDocumentVersions(documentId),
    getDocumentRelations(documentId),
  ])

  if (detailRes) {
    selectedDoc.value = {
      ...selectedDoc.value,
      id: detailRes.id,
      name: detailRes.documentName,
      type: detailRes.documentType,
      module: detailRes.module,
      cycle: detailRes.period,
      version: detailRes.version,
      source: detailRes.source,
      relatedTaskCount: detailRes.relationCount,
      status: detailRes.validityStatus as any,
      size: detailRes.file?.fileSizeText,
      uploadTime: detailRes.uploadedAt,
      creator: detailRes.responsibleUnit,
      format: detailRes.file?.fileExt?.toUpperCase(),
      tags: detailRes.tags,
      isUnique: detailRes.isUnique,
    }
  }

  if (versionsRes && versionsRes.items) {
    documentVersions.value = versionsRes.items
  }

  if (relationsRes && relationsRes.items) {
    selectedDoc.value.relatedTasks = relationsRes.items.map(item => ({
      module: item.module,
      name: item.taskName,
      cycle: item.cycle,
      status: item.status,
      referenceCount: item.referenceCount,
      lastReference: item.lastReference,
    }))
  }
}

function handlePreview() {
  showMessage('文件预览功能为原型预留，暂未接入真实文件预览服务。', 'info')
}

function handleViewVersion() {
  if (!documentVersions.value.length) {
    showMessage('暂无版本记录。', 'info')
    return
  }
  showMessage(documentVersions.value.map(v => `${v.versionNo}｜${v.versionDesc}｜${v.uploadedAt}`).join('；'), 'info')
}

function handleReuse() {
  showMessage('复用到其他任务功能为原型预留，后续接入跨任务资料复用流程。', 'info')
}
</script>

<template>
  <div class="workspace-documents">
    <div class="page-header">
      <div class="page-title">资料中心与档案</div>
      <div class="page-subtitle">统一入库、版本管理与跨流程复用</div>
    </div>

    <div v-if="pageMessage" :class="['page-message', pageMessageType]">
      {{ pageMessage }}
    </div>

    <div class="status-cards">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="status-card"
        :style="{ '--accent-color': card.color }"
      >
        <div class="card-icon">
          <Folder v-if="card.label === '资料总数'" :size="20" />
          <Tag v-else-if="card.label === '本月新增'" :size="20" />
          <Clock v-else-if="card.label === '待归档'" :size="20" />
          <FileText v-else-if="card.label === '即将失效'" :size="20" />
        </div>
        <div class="card-label">{{ card.label }}</div>
        <div class="card-value">{{ card.value }}</div>
        <div class="card-unit">{{ card.unit }}</div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-sidebar">
        <div class="category-section">
          <div class="section-title">资料分类</div>
          <div class="category-list">
            <button
              v-for="cat in computedCategories"
              :key="cat.label"
              :class="{ active: selectedCategory === cat.label }"
              @click="selectedCategory = cat.label"
            >
              <span class="category-name">{{ cat.label }}</span>
              <span class="category-count">{{ cat.value }}</span>
            </button>
          </div>
        </div>

        <div class="type-section">
          <div class="section-title">资料类型</div>
          <div class="type-list">
            <button
              v-for="type in computedTypes"
              :key="type.label"
              :class="{ active: selectedType === type.label }"
              @click="selectedType = selectedType === type.label ? '' : type.label"
            >
              <span class="type-name">{{ type.label }}</span>
              <span class="type-count">{{ type.value }}</span>
            </button>
          </div>
        </div>
      </div>

      <div class="middle-section">
        <div class="filter-bar">
          <div class="search-box">
            <Search :size="16" />
            <input v-model="searchKeyword" type="text" placeholder="请输入资料名称" />
          </div>
          <div class="filter-group">
            <span class="filter-label">资料周期</span>
            <select v-model="selectedCycle">
              <option value="">全部</option>
              <option value="2026-07">2026-07</option>
              <option value="2026年度">2026年度</option>
            </select>
          </div>
          <div class="filter-group">
            <span class="filter-label">来源</span>
            <select v-model="selectedSource">
              <option value="">全部</option>
              <option value="ESG智能入库">ESG智能入库</option>
              <option value="手动上传">手动上传</option>
            </select>
          </div>
          <div class="filter-group">
            <span class="filter-label">有效状态</span>
            <select v-model="selectedStatus">
              <option value="">全部</option>
              <option value="有效">有效</option>
              <option value="即将失效">即将失效</option>
              <option value="已失效">已失效</option>
            </select>
          </div>
          <button class="reset-btn" @click="handleReset">重置</button>
          <button class="filter-btn">筛选</button>
        </div>

        <div class="documents-table-wrapper">
          <table class="documents-table">
            <thead>
              <tr>
                <th>资料名称</th>
                <th>资料类型</th>
                <th>资料周期</th>
                <th>版本</th>
                <th>来源</th>
                <th>关联流程数</th>
                <th>有效状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="doc in filteredDocuments"
                :key="doc.id"
                :class="{ selected: selectedDoc?.id === doc.id }"
                @click="handleSelectDocument(doc)"
              >
                <td class="doc-name">
                  <FileText :size="16" class="doc-icon" />
                  {{ doc.name }}
                </td>
                <td>{{ doc.type }}</td>
                <td>{{ doc.cycle }}</td>
                <td>{{ doc.version }}</td>
                <td>{{ doc.source }}</td>
                <td>{{ doc.relatedTaskCount }}</td>
                <td>
                  <span class="status-tag" :style="{ color: getStatusColor(doc.status) }">
                    {{ doc.status }}
                  </span>
                </td>
                <td>
                  <button class="action-btn" @click.stop="handlePreview">预览</button>
                  <button class="action-btn" @click.stop="handleViewVersion">查看版本</button>
                  <button class="action-btn" @click.stop="handleReuse">复用</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pagination-bar">
          <div class="pagination-info">
            共 <span class="highlight">368</span> 条记录
          </div>
          <div class="pagination-controls">
            <button class="page-btn" disabled>上一页</button>
            <button class="page-btn active">1</button>
            <button class="page-btn">2</button>
            <button class="page-btn">3</button>
            <span class="page-ellipsis">...</span>
            <button class="page-btn">37</button>
            <button class="page-btn">下一页</button>
            <select class="page-size-select">
              <option>10条/页</option>
              <option>20条/页</option>
              <option>50条/页</option>
            </select>
          </div>
        </div>
      </div>

      <div class="right-sidebar">
        <div class="detail-card">
          <div class="card-header">
            <div class="card-title">资料详情与关联</div>
            <div class="green-tip">一个文件实体，多流程引用</div>
          </div>

          <div class="current-file">
            <FileText :size="24" class="file-icon" />
            <span class="file-name">{{ selectedDoc?.name }}</span>
          </div>

          <div class="detail-fields">
            <div class="detail-row">
              <span class="field-label">资料类型</span>
              <span class="field-value">{{ selectedDoc?.type }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">资料周期</span>
              <span class="field-value">{{ selectedDoc?.cycle }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">资料大小</span>
              <span class="field-value">{{ selectedDoc?.size }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">上传时间</span>
              <span class="field-value">{{ selectedDoc?.uploadTime }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">创建来源</span>
              <span class="field-value">{{ selectedDoc?.source }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">创建人</span>
              <span class="field-value">{{ selectedDoc?.creator }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">文件格式</span>
              <span class="field-value">{{ selectedDoc?.format }}</span>
            </div>
            <div class="detail-row">
              <span class="field-label">页数</span>
              <span class="field-value">{{ selectedDoc?.pages }} 页</span>
            </div>
          </div>

          <div class="tags-section">
            <div class="section-header">
              <span class="section-title">AI识别标签</span>
            </div>
            <div class="tags-list">
              <span
                v-for="tag in selectedDoc?.tags"
                :key="tag"
                class="tag-item"
              >{{ tag }}</span>
            </div>
          </div>

          <div class="duplicate-section">
            <div class="section-header">
              <span class="section-title">哈希去重状态</span>
            </div>
            <div class="duplicate-status" :class="{ unique: selectedDoc?.isUnique }">
              <span class="status-icon">✓</span>
              <span class="status-text">唯一文件，未发现重复</span>
            </div>
          </div>

          <div class="related-section">
            <div class="section-header">
              <span class="section-title">已关联任务（{{ selectedDoc?.relatedTasks?.length || 0 }}条）</span>
            </div>
            <div class="related-list">
              <div v-if="!selectedDoc?.relatedTasks?.length" class="empty-related">
                暂无关联任务
              </div>
              <div
                v-for="task in selectedDoc?.relatedTasks"
                :key="task.name"
                class="related-item"
              >
                <div class="related-item-header">
                  <span class="module-badge" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                    {{ task.module }}
                  </span>
                  <span class="task-name">{{ task.name }}</span>
                  <span class="task-status" :style="{ color: getStatusColor(task.status) }">{{ task.status }}</span>
                </div>
                <div class="related-item-details">
                  <span class="detail-item">
                    <Clock :size="12" />
                    周期：{{ task.cycle }}
                  </span>
                  <span class="detail-item">
                    <Link2 :size="12" />
                    引用：{{ task.referenceCount }} 次
                  </span>
                  <span class="detail-item">
                    <User :size="12" />
                    最近引用：{{ task.lastReference }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <button class="btn preview-btn" @click="handlePreview">预览</button>
            <button class="btn version-btn" @click="handleViewVersion">查看版本</button>
            <button class="btn reuse-btn" @click="handleReuse">复用到其他任务</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-documents {
  padding: 20px;
  height: calc(100% - 120px);
  overflow-y: auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #e8f3ff;
}

.page-subtitle {
  font-size: 13px;
  color: #8fa9c8;
  margin-top: 4px;
}

.page-message {
  margin: -6px 0 14px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}

.page-message.info {
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.3);
  color: #9fc7ff;
}

.page-message.success {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.page-message.error {
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  color: #ff4f5e;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.status-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 14px;
  text-align: center;
}

.card-icon {
  color: var(--accent-color);
  margin-bottom: 6px;
}

.card-label {
  font-size: 11px;
  color: #8fa9c8;
}

.card-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent-color);
}

.card-unit {
  font-size: 11px;
  color: #8fa9c8;
}

.main-content {
  display: flex;
  gap: 20px;
}

.left-sidebar {
  width: 220px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-section, .type-section {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 14px;
}

.section-title {
  font-size: 12px;
  color: #8fa9c8;
  margin-bottom: 10px;
}

.category-list, .type-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-list button, .type-list button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #e8f3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.category-list button:hover, .type-list button:hover {
  background: rgba(105, 227, 111, 0.08);
}

.category-list button.active {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.type-list button.active {
  background: rgba(105, 227, 111, 0.15);
}

.category-count, .type-count {
  font-size: 11px;
  color: #8fa9c8;
}

.middle-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #8fa9c8;
  min-width: 200px;
}

.search-box input {
  background: transparent;
  border: none;
  color: #e8f3ff;
  font-size: 12px;
  flex: 1;
  outline: none;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 12px;
  color: #8fa9c8;
}

.filter-group select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  padding: 6px 10px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  min-width: 120px;
}

.reset-btn {
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
}

.filter-btn {
  padding: 6px 16px;
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  border-radius: 4px;
  color: #031020;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.documents-table-wrapper {
  overflow-x: auto;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
}

.documents-table {
  width: 100%;
  border-collapse: collapse;
}

.documents-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.documents-table tr {
  cursor: pointer;
  transition: background 0.2s;
}

.documents-table tr:hover {
  background: rgba(105, 227, 111, 0.05);
}

.documents-table tr.selected {
  background: rgba(105, 227, 111, 0.1);
}

.documents-table td {
  padding: 12px 16px;
  font-size: 13px;
  color: #e8f3ff;
  border-bottom: 1px solid rgba(105, 227, 111, 0.05);
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  color: #8fa9c8;
}

.status-tag {
  font-size: 12px;
  font-weight: 500;
}

.action-btn {
  padding: 4px 8px;
  background: transparent;
  border: none;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  margin-right: 8px;
}

.action-btn:hover {
  color: #69e36f;
}

.pagination-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(5, 26, 50, 0.6);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-top: none;
  border-radius: 0 0 8px 8px;
}

.pagination-info {
  font-size: 12px;
  color: #8fa9c8;
}

.pagination-info .highlight {
  color: #69e36f;
  font-weight: 600;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-btn {
  padding: 4px 10px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #69e36f;
  color: #69e36f;
}

.page-btn.active {
  background: rgba(105, 227, 111, 0.2);
  border-color: #69e36f;
  color: #69e36f;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-ellipsis {
  color: #8fa9c8;
  font-size: 12px;
  padding: 0 4px;
}

.page-size-select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  padding: 4px 8px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  margin-left: 8px;
}

.right-sidebar {
  width: 380px;
}

.detail-card {
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.green-tip {
  font-size: 11px;
  color: #69e36f;
  padding: 4px 8px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 4px;
}

.current-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
}

.current-file .file-icon {
  color: #69e36f;
}

.current-file .file-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
}

.detail-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-label {
  font-size: 11px;
  color: #5a7a9a;
}

.field-value {
  font-size: 12px;
  color: #e8f3ff;
}

.tags-section, .duplicate-section, .related-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(105, 227, 111, 0.1);
}

.section-header {
  margin-bottom: 12px;
}

.section-title {
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  padding: 4px 10px;
  background: rgba(47, 156, 255, 0.15);
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 4px;
  font-size: 11px;
  color: #2f9cff;
}

.duplicate-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 6px;
}

.status-icon {
  width: 16px;
  height: 16px;
  background: #69e36f;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #031020;
}

.status-text {
  font-size: 12px;
  color: #e8f3ff;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-related {
  padding: 20px;
  text-align: center;
  color: #5a7a9a;
  font-size: 12px;
}

.related-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border: 1px solid rgba(105, 227, 111, 0.08);
}

.related-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.module-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.related-item .task-name {
  font-size: 12px;
  color: #e8f3ff;
  flex: 1;
  font-weight: 500;
}

.task-status {
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.related-item-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid rgba(105, 227, 111, 0.06);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #8fa9c8;
}

.detail-item svg {
  flex-shrink: 0;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  flex: 1;
  padding: 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.preview-btn {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.version-btn {
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.3);
  color: #2f9cff;
}

.reuse-btn {
  background: rgba(166, 108, 255, 0.1);
  border: 1px solid rgba(166, 108, 255, 0.3);
  color: #a66cff;
}
</style>
