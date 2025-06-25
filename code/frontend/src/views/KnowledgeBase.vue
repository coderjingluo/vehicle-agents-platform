<template>
  <div class="knowledge-base-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">Knowledge Base Manager</h1>
        <p class="page-description">Manage your knowledge bases, upload documents, and explore content</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          New Knowledge Base
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          Refresh
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content-area">
      <!-- 左侧知识库列表 -->
      <div class="knowledge-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">Knowledge Bases</h3>
          <span class="kb-count">{{ knowledgeBases.length }}</span>
        </div>
        <div class="kb-list">
          <div
            v-for="kb in knowledgeBases"
            :key="kb.name"
            class="kb-item"
            :class="{ active: selectedKB === kb.name }"
            @click="selectKnowledgeBase(kb.name)"
          >
            <div class="kb-icon">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="kb-info">
              <div class="kb-name">{{ kb.name }}</div>
              <div class="kb-meta">
                <span class="doc-count">{{ kb.docCount }} docs</span>
                <span class="status" :class="kb.status">{{ kb.status }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧内容区域 -->
      <div class="content-main">
        <div v-if="!selectedKB" class="empty-state">
          <el-icon class="empty-icon"><Document /></el-icon>
          <h3>Select a knowledge base to manage</h3>
          <p>Choose a knowledge base from the left sidebar to view and manage its content</p>
        </div>

        <div v-else class="kb-content">
          <!-- 选项卡 -->
          <el-tabs v-model="activeTab" class="content-tabs">
            <el-tab-pane label="Documents" name="documents">
              <div class="documents-section">
                <div class="documents-toolbar">
                  <el-input
                    v-model="searchText"
                    placeholder="Search documents..."
                    class="search-input"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                  <el-select v-model="sortBy" placeholder="Sort by" class="sort-select">
                    <el-option label="Name" value="name" />
                    <el-option label="Date Added" value="date" />
                    <el-option label="Size" value="size" />
                  </el-select>
                </div>

                <div class="documents-grid">
                  <div
                    v-for="doc in filteredDocuments"
                    :key="doc.id"
                    class="document-card"
                    @click="viewDocument(doc)"
                  >
                    <div class="doc-icon">
                      <el-icon><component :is="getDocumentIcon(doc.type)" /></el-icon>
                    </div>
                    <div class="doc-info">
                      <h4 class="doc-name">{{ doc.name }}</h4>
                      <div class="doc-meta">
                        <span class="doc-chunks">{{ doc.chunks }} chunks</span>
                        <span class="doc-date">{{ formatDate(doc.addedDate) }}</span>
                      </div>
                      <div class="doc-preview">{{ doc.preview }}</div>
                    </div>
                    <div class="doc-actions" @click.stop>
                      <el-button text size="small" @click="viewDocument(doc)">
                        <el-icon><View /></el-icon>
                      </el-button>
                      <el-button text size="small" @click="deleteDocument(doc)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Search" name="search">
              <div class="search-section">
                <div class="search-input-area">
                  <el-input
                    v-model="searchQuery"
                    type="textarea"
                    :autosize="{ minRows: 3, maxRows: 6 }"
                    placeholder="Enter your search query here..."
                    class="search-textarea"
                  />
                  <el-button type="primary" @click="performSearch" :loading="searching">
                    <el-icon><Search /></el-icon>
                    Search
                  </el-button>
                </div>

                <div v-if="searchResults.length > 0" class="search-results">
                  <h4 class="results-title">Search Results ({{ searchResults.length }})</h4>
                  <div class="results-list">
                    <div
                      v-for="result in searchResults"
                      :key="result.id"
                      class="result-item"
                    >
                      <div class="result-header">
                        <h5 class="result-title">{{ result.title }}</h5>
                        <span class="result-score">{{ (result.score * 100).toFixed(1) }}%</span>
                      </div>
                      <div class="result-content" v-html="result.highlightedContent"></div>
                      <div class="result-meta">
                        <span class="result-source">{{ result.source }}</span>
                        <span class="result-chunk">Chunk {{ result.chunkIndex }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Upload" name="upload">
              <div class="upload-section">
                <el-upload
                  class="upload-dragger"
                  drag
                  :action="uploadUrl"
                  multiple
                  :before-upload="beforeUpload"
                  :on-success="onUploadSuccess"
                  :on-error="onUploadError"
                  :show-file-list="false"
                >
                  <el-icon class="upload-icon"><UploadFilled /></el-icon>
                  <div class="upload-text">
                    <p class="upload-title">Drop files here or click to upload</p>
                    <p class="upload-hint">Support for PDF, TXT, DOCX, MD files</p>
                  </div>
                </el-upload>

                <div v-if="uploadQueue.length > 0" class="upload-queue">
                  <h4 class="queue-title">Upload Queue</h4>
                  <div class="queue-list">
                    <div
                      v-for="file in uploadQueue"
                      :key="file.id"
                      class="queue-item"
                    >
                      <div class="file-icon">
                        <el-icon><component :is="getFileIcon(file.name)" /></el-icon>
                      </div>
                      <div class="file-info">
                        <div class="file-name">{{ file.name }}</div>
                        <div class="file-size">{{ formatFileSize(file.size) }}</div>
                      </div>
                      <div class="upload-progress">
                        <el-progress
                          :percentage="file.progress"
                          :status="file.status"
                          :show-text="false"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="Create New Knowledge Base"
      width="500px"
    >
      <el-form :model="newKBForm" label-width="120px">
        <el-form-item label="Name" required>
          <el-input v-model="newKBForm.name" placeholder="Enter knowledge base name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="newKBForm.description"
            type="textarea"
            :autosize="{ minRows: 3 }"
            placeholder="Enter description"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">Cancel</el-button>
        <el-button type="primary" @click="createKnowledgeBase">Create</el-button>
      </template>
    </el-dialog>

    <!-- 文档详情对话框 -->
    <el-dialog
      v-model="showDocumentDialog"
      :title="selectedDocument?.name"
      width="80%"
      class="document-dialog"
    >
      <el-tabs v-model="docDetailTab">
        <el-tab-pane label="Preview" name="preview">
          <div class="doc-preview-content">
            {{ selectedDocument?.content || 'No preview available' }}
          </div>
        </el-tab-pane>
        <el-tab-pane label="Chunks" name="chunks">
          <div class="doc-chunks-list">
            <div
              v-for="(chunk, index) in selectedDocument?.chunks || []"
              :key="index"
              class="chunk-item"
            >
              <div class="chunk-header">
                <span class="chunk-index">Chunk {{ index + 1 }}</span>
                <span class="chunk-tokens">{{ chunk.tokens }} tokens</span>
              </div>
              <div class="chunk-content">{{ chunk.content }}</div>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="Metadata" name="metadata">
          <div class="doc-metadata">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="File Name">{{ selectedDocument?.name }}</el-descriptions-item>
              <el-descriptions-item label="File Type">{{ selectedDocument?.type }}</el-descriptions-item>
              <el-descriptions-item label="File Size">{{ selectedDocument?.size }}</el-descriptions-item>
              <el-descriptions-item label="Chunks">{{ selectedDocument?.chunks }}</el-descriptions-item>
              <el-descriptions-item label="Added Date">{{ formatDate(selectedDocument?.addedDate) }}</el-descriptions-item>
              <el-descriptions-item label="Last Modified">{{ formatDate(selectedDocument?.modifiedDate) }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Plus, Refresh, Folder, Document, Search, UploadFilled, View, Delete,
  DocumentCopy, Picture, VideoPlay
} from '@element-plus/icons-vue'

// 响应式数据
const selectedKB = ref(null)
const activeTab = ref('documents')
const searchQuery = ref('')
const searchText = ref('')
const sortBy = ref('name')
const searching = ref(false)
const searchResults = ref([])
const showDocumentDialog = ref(false)
const showCreateDialog = ref(false)
const selectedDocument = ref(null)
const docDetailTab = ref('preview')
const uploadQueue = ref([])

const newKBForm = ref({
  name: '',
  description: ''
})

// 模拟数据
const knowledgeBases = ref([
  {
    name: 'default',
    docCount: 1,
    status: 'ready'
  },
  {
    name: 'ctf_notes',
    docCount: 0,
    status: 'empty'
  },
  {
    name: 'ctf',
    docCount: 552,
    status: 'ready'
  }
])

const documents = ref([
  {
    id: '1',
    name: '知识库文档列表',
    type: 'document',
    chunks: 552,
    addedDate: '2025/6/17',
    preview: 'No preview available',
    content: '这是文档的预览内容...',
    size: '12KB'
  },
  {
    id: '2',
    name: 'PHP_RCE.md',
    type: 'markdown',
    chunks: 9,
    addedDate: '2025/6/10',
    preview: 'PHP Remote Code Execution vulnerabilities...',
    content: '# PHP RCE 漏洞\n\n这是关于PHP远程代码执行漏洞的文档...',
    size: '8KB'
  },
  {
    id: '3',
    name: 'image_20231211658337174.txt',
    type: 'text',
    chunks: 375,
    addedDate: '2025/6/10',
    preview: 'Security analysis report containing...',
    content: '安全分析报告内容...',
    size: '45KB'
  },
  {
    id: '4',
    name: 'image_20231211701283834.txt',
    type: 'text',
    chunks: 23,
    addedDate: '2025/6/10',
    preview: 'Technical documentation for...',
    content: '技术文档内容...',
    size: '15KB'
  }
])

// 计算属性
const filteredDocuments = computed(() => {
  let filtered = documents.value
  
  if (searchText.value) {
    filtered = filtered.filter(doc => 
      doc.name.toLowerCase().includes(searchText.value.toLowerCase())
    )
  }
  
  // 排序
  if (sortBy.value === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name))
  } else if (sortBy.value === 'date') {
    filtered.sort((a, b) => new Date(b.addedDate) - new Date(a.addedDate))
  }
  
  return filtered
})

const uploadUrl = computed(() => '/api/v1/knowledge-base/upload')

// 方法
const selectKnowledgeBase = (kbName) => {
  selectedKB.value = kbName
  activeTab.value = 'documents'
}

const createKnowledgeBase = () => {
  if (!newKBForm.value.name) {
    ElMessage.warning('Please enter knowledge base name')
    return
  }
  
  ElMessage.success('Knowledge base created successfully!')
  showCreateDialog.value = false
  newKBForm.value = { name: '', description: '' }
}

const refreshData = () => {
  ElMessage.success('Data refreshed')
}

const viewDocument = (doc) => {
  selectedDocument.value = doc
  showDocumentDialog.value = true
  docDetailTab.value = 'preview'
}

const deleteDocument = (doc) => {
  ElMessage.success(`Document "${doc.name}" deleted`)
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) return
  
  searching.value = true
  // 模拟搜索延迟
  setTimeout(() => {
    searchResults.value = [
      {
        id: 1,
        title: 'Search Result 1',
        score: 0.95,
        source: 'PHP_RCE.md',
        chunkIndex: 1,
        highlightedContent: `This is a <mark>highlighted</mark> search result containing ${searchQuery.value}...`
      },
      {
        id: 2,
        title: 'Search Result 2',
        score: 0.87,
        source: '知识库文档列表',
        chunkIndex: 3,
        highlightedContent: `Another search result with <mark>relevant</mark> content about ${searchQuery.value}...`
      }
    ]
    searching.value = false
  }, 1500)
}

const formatDate = (dateStr) => {
  return dateStr
}

const formatFileSize = (size) => {
  if (typeof size === 'string') return size
  return (size / 1024).toFixed(1) + ' KB'
}

const getDocumentIcon = (type) => {
  switch (type) {
    case 'image': return 'Picture'
    case 'video': return 'VideoPlay'
    case 'text': return 'DocumentCopy'
    case 'markdown': return 'Document'
    default: return 'Document'
  }
}

const getFileIcon = (fileName) => {
  const ext = fileName.split('.').pop().toLowerCase()
  switch (ext) {
    case 'pdf': return 'Document'
    case 'txt': return 'DocumentCopy'
    case 'md': return 'Document'
    case 'docx': return 'Document'
    default: return 'Document'
  }
}

const beforeUpload = (file) => {
  const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/markdown']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('Only PDF, TXT, DOCX, MD files are supported!')
    return false
  }
  return true
}

const onUploadSuccess = (response, file) => {
  ElMessage.success(`${file.name} uploaded successfully!`)
  // 刷新文档列表
}

const onUploadError = (error, file) => {
  ElMessage.error(`${file.name} upload failed!`)
}

// 生命周期
onMounted(() => {
  // 默认选择第一个知识库
  if (knowledgeBases.value.length > 0) {
    selectedKB.value = knowledgeBases.value[0]
  }
})
</script>

<style scoped>
.knowledge-base-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

/* ========== 页面标题 ========== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}

.header-content h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* ========== 主要内容区域 ========== */
.main-content-area {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* ========== 左侧边栏 ========== */
.knowledge-sidebar {
  width: 280px;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.kb-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  padding: 2px 8px;
  border-radius: 10px;
}

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 4px;
}

.kb-item:hover {
  background: var(--el-fill-color-light);
}

.kb-item.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.kb-icon {
  color: var(--el-color-primary);
  font-size: 18px;
}

.kb-info {
  flex: 1;
  min-width: 0;
}

.kb-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.kb-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.status.ready {
  color: var(--el-color-success);
}

.status.empty {
  color: var(--el-color-warning);
}

/* ========== 右侧内容区域 ========== */
.content-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 64px;
  color: var(--el-border-color-darker);
  margin-bottom: 16px;
}

.kb-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.content-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

/* ========== 文档部分 ========== */
.documents-section {
  height: 100%;
  padding: 20px;
}

.documents-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  flex: 1;
}

.sort-select {
  width: 140px;
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.document-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.document-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.doc-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  margin-bottom: 8px;
}

.doc-name {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.doc-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.doc-preview {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.doc-actions {
  display: flex;
  gap: 4px;
  margin-top: 12px;
}

/* ========== 搜索部分 ========== */
.search-section {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.search-input-area {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-textarea {
  flex: 1;
}

.results-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-item {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 16px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.result-score {
  font-size: 12px;
  color: var(--el-color-success);
  font-weight: 500;
}

.result-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--el-text-color-regular);
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* ========== 上传部分 ========== */
.upload-section {
  padding: 20px;
  height: 100%;
  overflow-y: auto;
}

.upload-dragger {
  width: 100%;
}

.upload-icon {
  font-size: 48px;
  color: var(--el-text-color-secondary);
  margin-bottom: 16px;
}

.upload-title {
  font-size: 16px;
  color: var(--el-text-color-primary);
  margin: 0 0 8px 0;
}

.upload-hint {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.upload-queue {
  margin-top: 24px;
}

.queue-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
}

.file-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.file-size {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.upload-progress {
  width: 120px;
}

/* ========== 对话框样式 ========== */
.document-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.doc-preview-content {
  padding: 20px;
  white-space: pre-wrap;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.doc-chunks-list {
  padding: 20px;
}

.chunk-item {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 16px;
  overflow: hidden;
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color);
}

.chunk-index {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.chunk-tokens {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.chunk-content {
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.doc-metadata {
  padding: 20px;
}

/* ========== 响应式设计 ========== */
@media (max-width: 1024px) {
  .main-content-area {
    flex-direction: column;
  }
  
  .knowledge-sidebar {
    width: 100%;
    height: 200px;
  }
  
  .documents-grid {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px;
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .documents-toolbar {
    flex-direction: column;
  }
  
  .search-input-area {
    flex-direction: column;
  }
}
</style> 