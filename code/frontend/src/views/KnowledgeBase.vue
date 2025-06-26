<template>
  <div class="knowledge-base-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">Knowledge Base Manager</h1>
        <p class="page-description">Manage your knowledge bases, upload documents, and explore content</p>
      </div>
      <div class="header-actions">
        <el-button @click="showStatsDialog = true">
          <el-icon><DataAnalysis /></el-icon>
          Statistics
        </el-button>
        <el-button @click="exportKnowledgeBase" :disabled="!selectedKB">
          <el-icon><Download /></el-icon>
          Export
        </el-button>
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          Import
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          New Knowledge Base
        </el-button>
        <el-button @click="refreshData" :loading="refreshing">
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
            @contextmenu.prevent="showKBContextMenu($event, kb)"
          >
            <div class="kb-icon">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="kb-info">
              <div class="kb-name">{{ kb.name }}</div>
              <div class="kb-meta">
                <span class="doc-count">{{ kb.docCount }} docs</span>
                <span class="kb-size">{{ formatFileSize(kb.totalSize || 0) }}</span>
                <span class="status" :class="kb.status">{{ kb.status }}</span>
              </div>
            </div>
            <div class="kb-actions" @click.stop>
              <el-dropdown trigger="click" @command="handleKBAction">
                <el-button text size="small">
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'edit', kb}">
                      <el-icon><Edit /></el-icon>
                      Edit
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'settings', kb}">
                      <el-icon><Setting /></el-icon>
                      Settings
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'duplicate', kb}">
                      <el-icon><CopyDocument /></el-icon>
                      Duplicate
                    </el-dropdown-item>
                    <el-dropdown-item :command="{action: 'delete', kb}" divided>
                      <el-icon><Delete /></el-icon>
                      Delete
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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
          <el-tabs v-model="activeTab" class="content-tabs" type="card">
            <el-tab-pane label="Documents" name="documents">
              <div class="documents-section">
                <div class="documents-toolbar">
                  <div class="toolbar-left">
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
                      <el-option label="Chunks" value="chunks" />
                    </el-select>
                  </div>
                  <div class="toolbar-right">
                    <el-button-group>
                      <el-button 
                        :type="viewMode === 'grid' ? 'primary' : ''" 
                        @click="viewMode = 'grid'"
                        size="small"
                      >
                        <el-icon><Grid /></el-icon>
                      </el-button>
                      <el-button 
                        :type="viewMode === 'list' ? 'primary' : ''" 
                        @click="viewMode = 'list'"
                        size="small"
                      >
                        <el-icon><List /></el-icon>
                      </el-button>
                    </el-button-group>
                    <el-button @click="selectAll" size="small">
                      {{ selectedDocs.length === filteredDocuments.length ? 'Deselect All' : 'Select All' }}
                    </el-button>
                    <el-button 
                      @click="batchDelete" 
                      :disabled="selectedDocs.length === 0"
                      type="danger"
                      size="small"
                    >
                      <el-icon><Delete /></el-icon>
                      Delete ({{ selectedDocs.length }})
                    </el-button>
                  </div>
                </div>

                <!-- 网格视图 -->
                <div v-if="viewMode === 'grid'" class="documents-grid-container">
                  <div class="documents-grid">
                    <div
                      v-for="doc in filteredDocuments"
                      :key="doc.id"
                      class="document-card"
                      :class="{ selected: selectedDocs.includes(doc.id) }"
                      @click="toggleDocSelection(doc.id)"
                    >
                      <div class="doc-checkbox">
                        <el-checkbox 
                          :model-value="selectedDocs.includes(doc.id)" 
                          @change="toggleDocSelection(doc.id)"
                          @click.stop
                        />
                      </div>
                      <div class="doc-icon">
                        <el-icon><component :is="getDocumentIcon(doc.type)" /></el-icon>
                      </div>
                      <div class="doc-info">
                        <h4 class="doc-name">{{ doc.name }}</h4>
                        <div class="doc-meta">
                          <span class="doc-chunks">{{ doc.chunks }} chunks</span>
                          <span class="doc-size">{{ formatFileSize(doc.size) }}</span>
                          <span class="doc-date">{{ formatDate(doc.addedDate) }}</span>
                        </div>
                        <div class="doc-preview">{{ doc.preview }}</div>
                      </div>
                      <div class="doc-actions" @click.stop>
                        <el-button text size="small" @click="viewDocument(doc)">
                          <el-icon><View /></el-icon>
                        </el-button>
                        <el-button text size="small" @click="editDocument(doc)">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                        <el-button text size="small" @click="deleteDocument(doc)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 列表视图 -->
                <div v-else class="documents-list">
                  <el-table
                    :data="filteredDocuments"
                    @selection-change="handleSelectionChange"
                    @row-click="viewDocument"
                  >
                    <el-table-column type="selection" width="55" />
                    <el-table-column prop="name" label="Name" min-width="200">
                      <template #default="{ row }">
                        <div class="doc-name-cell">
                          <el-icon class="doc-type-icon">
                            <component :is="getDocumentIcon(row.type)" />
                          </el-icon>
                          <span>{{ row.name }}</span>
                        </div>
                      </template>
                    </el-table-column>
                    <el-table-column prop="chunks" label="Chunks" width="100" sortable />
                    <el-table-column prop="size" label="Size" width="100" sortable>
                      <template #default="{ row }">
                        {{ formatFileSize(row.size) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="addedDate" label="Added" width="120" sortable />
                    <el-table-column label="Actions" width="120">
                      <template #default="{ row }">
                        <el-button text size="small" @click.stop="viewDocument(row)">
                          <el-icon><View /></el-icon>
                        </el-button>
                        <el-button text size="small" @click.stop="editDocument(row)">
                          <el-icon><Edit /></el-icon>
                        </el-button>
                        <el-button text size="small" @click.stop="deleteDocument(row)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Search" name="search">
              <div class="search-section">
                <div class="search-header">
                  <div class="search-title">
                    <el-icon><Search /></el-icon>
                    <span>Search Documents</span>
                  </div>
                  <div class="search-description">
                    Search through all documents in this knowledge base
                  </div>
                </div>

                <div class="search-input-area">
                  <el-input
                    v-model="searchQuery"
                    placeholder="Enter search terms..."
                    class="search-input-box"
                    clearable
                  >
                    <template #suffix>
                      <el-button 
                        type="primary" 
                        @click="performSearch" 
                        :loading="searching"
                        :disabled="!searchQuery.trim()"
                        size="small"
                        style="margin-right: 8px;"
                      >
                        <el-icon><Search /></el-icon>
                      </el-button>
                    </template>
                  </el-input>
                </div>

                <div class="search-stats" v-if="searchResults.length > 0">
                  <el-icon><Document /></el-icon>
                  <span>{{ searchResults.length }} results</span>
                  <el-icon><Timer /></el-icon>
                  <span>669ms</span>
                </div>

                <div v-if="searchResults.length > 0" class="search-results">
                  <div class="results-title">Search Results</div>
                  <div class="results-list">
                    <div
                      v-for="result in searchResults"
                      :key="result.id"
                      class="result-item"
                    >
                      <div class="result-header">
                        <div class="result-title-section">
                          <el-icon class="result-icon"><Document /></el-icon>
                          <span class="result-title">{{ result.title }}</span>
                        </div>
                        <div class="result-meta-section">
                          <span class="result-score">{{ (result.score * 100).toFixed(1) }}% match</span>
                        </div>
                      </div>
                      <div class="result-chunk-info">
                        <span>Chunk {{ result.chunkIndex }}</span>
                        <span>•</span>
                        <span>Added {{ result.source }}</span>
                      </div>
                      <div class="result-content" v-html="result.highlightedContent"></div>
                      <div class="result-actions">
                        <el-button text size="small">
                          <el-icon><View /></el-icon>
                          View Document
                        </el-button>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-else-if="searchQuery && !searching" class="empty-results">
                  <el-icon class="empty-icon"><Search /></el-icon>
                  <div class="empty-text">No results found</div>
                  <div class="empty-hint">Try different keywords or check spelling</div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Upload" name="upload">
              <div class="upload-section">
                <div class="upload-header">
                  <div class="upload-title">
                    <el-icon><UploadFilled /></el-icon>
                    <span>Upload Documents</span>
                  </div>
                  <div class="upload-description">
                    Add new documents to your knowledge base
                  </div>
                </div>

                <div class="upload-area">
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
                      <p class="upload-main-text">Drop files here or click to upload</p>
                      <p class="upload-hint">Support for PDF, TXT, DOCX, MD files</p>
                    </div>
                  </el-upload>
                </div>

                <div class="upload-options">
                  <div class="options-title">Upload Options</div>
                  <div class="options-grid">
                    <div class="option-item">
                      <el-switch v-model="uploadSettings.autoProcess" />
                      <div class="option-info">
                        <div class="option-label">Auto Process</div>
                        <div class="option-desc">Automatically process uploaded files</div>
                      </div>
                    </div>
                    <div class="option-item">
                      <el-switch v-model="uploadSettings.extractMetadata" />
                      <div class="option-info">
                        <div class="option-label">Extract Metadata</div>
                        <div class="option-desc">Extract file metadata and properties</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div v-if="uploadQueue.length > 0" class="upload-queue">
                  <div class="queue-header">
                    <div class="queue-title">
                      <el-icon><Document /></el-icon>
                      <span>Upload Queue ({{ uploadQueue.length }})</span>
                    </div>
                    <el-button text size="small" @click="clearQueue">
                      Clear All
                    </el-button>
                  </div>
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
                        <div class="file-meta">
                          <span class="file-size">{{ formatFileSize(file.size) }}</span>
                          <span class="file-status" :class="file.status">{{ file.status || 'pending' }}</span>
                        </div>
                      </div>
                      <div class="upload-progress">
                        <el-progress
                          :percentage="file.progress || 0"
                          :status="file.status === 'error' ? 'exception' : (file.status === 'success' ? 'success' : '')"
                          :show-text="false"
                          :stroke-width="4"
                        />
                      </div>
                      <div class="file-actions">
                        <el-button text size="small" @click="removeFromQueue(file.id)">
                          <el-icon><Delete /></el-icon>
                        </el-button>
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

    <!-- 知识库编辑对话框 -->
    <el-dialog
      v-model="showEditKBDialog"
      title="Edit Knowledge Base"
      width="500px"
    >
      <el-form :model="editKBForm" label-width="120px">
        <el-form-item label="Name" required>
          <el-input v-model="editKBForm.name" placeholder="Enter knowledge base name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input
            v-model="editKBForm.description"
            type="textarea"
            :autosize="{ minRows: 3 }"
            placeholder="Enter description"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditKBDialog = false">Cancel</el-button>
        <el-button type="primary" @click="updateKnowledgeBase">Update</el-button>
      </template>
    </el-dialog>

    <!-- 知识库设置对话框 -->
    <el-dialog
      v-model="showKBSettingsDialog"
      title="Knowledge Base Settings"
      width="600px"
    >
      <el-form :model="kbSettings" label-width="150px">
        <el-form-item label="Chunk Size">
          <el-input-number v-model="kbSettings.chunkSize" :min="100" :max="2000" />
        </el-form-item>
        <el-form-item label="Chunk Overlap">
          <el-input-number v-model="kbSettings.chunkOverlap" :min="0" :max="500" />
        </el-form-item>
        <el-form-item label="Embedding Model">
          <el-select v-model="kbSettings.embeddingModel" style="width: 100%">
            <el-option label="text-embedding-ada-002" value="text-embedding-ada-002" />
            <el-option label="text-embedding-3-small" value="text-embedding-3-small" />
            <el-option label="text-embedding-3-large" value="text-embedding-3-large" />
          </el-select>
        </el-form-item>
        <el-form-item label="Auto Processing">
          <el-switch v-model="kbSettings.autoProcessing" />
        </el-form-item>
        <el-form-item label="Index Updates">
          <el-switch v-model="kbSettings.autoIndexing" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showKBSettingsDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveKBSettings">Save Settings</el-button>
      </template>
    </el-dialog>

    <!-- 统计信息对话框 -->
    <el-dialog
      v-model="showStatsDialog"
      title="Knowledge Base Statistics"
      width="800px"
    >
      <div class="stats-content">
        <el-row :gutter="16">
          <el-col :span="8">
            <el-card>
              <el-statistic title="Total Knowledge Bases" :value="knowledgeBases.length" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic title="Total Documents" :value="totalDocuments" />
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card>
              <el-statistic title="Total Size" :value="totalSize" suffix="MB" />
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="16" style="margin-top: 16px;">
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>Storage Usage by Type</span>
              </template>
              <div class="chart-placeholder">Chart placeholder</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card>
              <template #header>
                <span>Document Activity</span>
              </template>
              <div class="chart-placeholder">Chart placeholder</div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>

    <!-- 导入对话框 -->
    <el-dialog
      v-model="showImportDialog"
      title="Import Knowledge Base"
      width="500px"
    >
      <el-upload
        class="upload-demo"
        drag
        :action="importUrl"
        :before-upload="beforeImport"
        :on-success="onImportSuccess"
        :show-file-list="false"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p>Drop knowledge base file here or click to upload</p>
          <p class="upload-hint">Support for .zip and .json files</p>
        </div>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Refresh, Folder, Document, Search, UploadFilled, View, Delete,
  DocumentCopy, Picture, VideoPlay, Edit, Setting, More, CopyDocument,
  DataAnalysis, Download, Upload, Grid, List, Timer
} from '@element-plus/icons-vue'

// API imports
import knowledgeAPI from '../api/modules/knowledge'

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
const showEditKBDialog = ref(false)
const showKBSettingsDialog = ref(false)
const showStatsDialog = ref(false)
const showImportDialog = ref(false)
const selectedDocument = ref(null)
const docDetailTab = ref('preview')
const uploadQueue = ref([])
const refreshing = ref(false)
const viewMode = ref('grid')
const selectedDocs = ref([])

// 加载状态
const loading = ref(false)
const uploading = ref(false)

const newKBForm = ref({
  name: '',
  description: '',
  type: 'general'
})

const editKBForm = ref({
  name: '',
  description: ''
})

const kbSettings = ref({
  chunkSize: 1000,
  chunkOverlap: 200,
  embeddingModel: 'text-embedding-ada-002',
  autoProcessing: true,
  autoIndexing: true
})

const uploadSettings = ref({
  autoProcess: true,
  extractMetadata: true
})

// 数据存储
const knowledgeBases = ref([])
const documents = ref([])
const statsData = ref({})

// 计算属性
const filteredDocuments = computed(() => {
  let filtered = documents.value
  
  if (searchText.value) {
    filtered = filtered.filter(doc => 
      doc.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
      (doc.preview && doc.preview.toLowerCase().includes(searchText.value.toLowerCase()))
    )
  }
  
  // 排序
  if (sortBy.value === 'name') {
    filtered.sort((a, b) => a.name.localeCompare(b.name))
  } else if (sortBy.value === 'date') {
    filtered.sort((a, b) => new Date(b.addedDate || b.created_at) - new Date(a.addedDate || a.created_at))
  } else if (sortBy.value === 'size') {
    filtered.sort((a, b) => {
      const sizeA = typeof a.size === 'string' ? parseInt(a.size) : (a.size || 0)
      const sizeB = typeof b.size === 'string' ? parseInt(b.size) : (b.size || 0)
      return sizeB - sizeA
    })
  } else if (sortBy.value === 'chunks') {
    filtered.sort((a, b) => (b.chunks || 0) - (a.chunks || 0))
  }
  
  return filtered
})

const uploadUrl = computed(() => {
  if (selectedKB.value) {
    return `/api/v1/knowledge-bases/${selectedKB.value}/documents`
  }
  return null
})

const importUrl = computed(() => '/api/v1/knowledge-bases/import')

const totalDocuments = computed(() => {
  return knowledgeBases.value.reduce((sum, kb) => sum + (kb.docCount || 0), 0)
})

const totalSize = computed(() => {
  const bytes = knowledgeBases.value.reduce((sum, kb) => sum + (kb.totalSize || 0), 0)
  return (bytes / (1024 * 1024)).toFixed(1)
})

// 获取知识库列表
const fetchKnowledgeBases = async () => {
  try {
    loading.value = true
    const response = await knowledgeAPI.getKnowledgeBases()
    
    if (response.data?.success !== false) {
      // 处理不同的响应格式
      const kbData = response.data?.knowledge_bases || response.data || []
      
      knowledgeBases.value = kbData.map(kb => ({
        id: kb.id,
        name: kb.name,
        description: kb.description || '默认描述',
        docCount: kb.document_count || kb.docCount || 0,
        totalSize: kb.total_size || kb.totalSize || 0,
        status: kb.status || 'ready',
        created_at: kb.created_at,
        updated_at: kb.updated_at
      }))
      
      // 如果没有选中的知识库且有知识库存在，选择第一个
      if (!selectedKB.value && knowledgeBases.value.length > 0) {
        selectedKB.value = knowledgeBases.value[0].id
        await fetchDocuments()
      }
    }
  } catch (error) {
    console.error('获取知识库列表失败:', error)
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

// 获取文档列表
const fetchDocuments = async () => {
  if (!selectedKB.value) return
  
  try {
    loading.value = true
    const response = await knowledgeAPI.getDocuments(selectedKB.value)
    
    if (response.data?.success !== false) {
      const docsData = response.data?.documents || response.data || []
      
      documents.value = docsData.map(doc => ({
        id: doc.id,
        name: doc.filename || doc.name,
        type: getDocumentType(doc.filename || doc.name),
        chunks: doc.chunk_count || doc.chunks || 0,
        addedDate: doc.created_at || doc.addedDate,
        preview: doc.preview || doc.summary || '无预览',
        content: doc.content || '',
        size: doc.file_size || doc.size || 0
      }))
    }
  } catch (error) {
    console.error('获取文档列表失败:', error)
    ElMessage.error('获取文档列表失败')
  } finally {
    loading.value = false
  }
}

// 获取统计信息
const fetchStats = async () => {
  try {
    const response = await knowledgeAPI.getStats()
    if (response.data?.success !== false) {
      statsData.value = response.data?.stats || response.data || {}
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

// 方法
const selectKnowledgeBase = async (kbId) => {
  if (selectedKB.value === kbId) return
  
  selectedKB.value = kbId
  activeTab.value = 'documents'
  selectedDocs.value = [] // 重置选中的文档
  
  await fetchDocuments()
}

const createKnowledgeBase = async () => {
  if (!newKBForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  
  try {
    loading.value = true
    const response = await knowledgeAPI.createKnowledgeBase({
      name: newKBForm.value.name.trim(),
      description: newKBForm.value.description.trim(),
      type: newKBForm.value.type || 'general'
    })
    
    if (response.data?.success !== false) {
      ElMessage.success('知识库创建成功')
      showCreateDialog.value = false
      newKBForm.value = { name: '', description: '', type: 'general' }
      
      // 刷新知识库列表
      await fetchKnowledgeBases()
    } else {
      throw new Error(response.data?.message || '创建失败')
    }
  } catch (error) {
    console.error('创建知识库失败:', error)
    ElMessage.error(`创建失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      fetchKnowledgeBases(),
      fetchStats()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('数据刷新失败')
  } finally {
    refreshing.value = false
  }
}

// 文档操作
const viewDocument = (doc) => {
  selectedDocument.value = doc
  showDocumentDialog.value = true
  docDetailTab.value = 'preview'
}

const editDocument = (doc) => {
  // 实现文档编辑功能
  ElMessage.info('文档编辑功能开发中')
}

const deleteDocument = async (doc) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档"${doc.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await knowledgeAPI.deleteDocument(selectedKB.value, doc.id)
    ElMessage.success('文档删除成功')
    
    // 刷新文档列表
    await fetchDocuments()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文档失败:', error)
      ElMessage.error('删除文档失败')
    }
  }
}

const batchDelete = async () => {
  if (selectedDocs.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDocs.value.length} 个文档吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 批量删除文档
    const promises = selectedDocs.value.map(docId => 
      knowledgeAPI.deleteDocument(selectedKB.value, docId)
    )
    
    await Promise.all(promises)
    ElMessage.success(`成功删除 ${selectedDocs.value.length} 个文档`)
    
    selectedDocs.value = []
    await fetchDocuments()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 搜索功能
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  try {
    searching.value = true
    
    const searchParams = {
      query: searchQuery.value.trim(),
      knowledge_base_ids: selectedKB.value ? [selectedKB.value] : [],
      top_k: 20,
      score_threshold: 0.3
    }
    
    const response = await knowledgeAPI.search(searchParams)
    
    if (response.data?.success !== false) {
      const results = response.data?.results || response.data || []
      
      searchResults.value = results.map((result, index) => ({
        id: result.id || index,
        title: result.title || `搜索结果 ${index + 1}`,
        score: result.score || result.similarity || 0,
        source: result.source || result.document_name || '未知来源',
        chunkIndex: result.chunk_index || result.chunk_id || 0,
        highlightedContent: result.content || result.text || '',
        metadata: result.metadata || {}
      }))
    }
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

// 文件上传
const handleFileUpload = async (file) => {
  if (!selectedKB.value) {
    ElMessage.warning('请先选择知识库')
    return false
  }
  
  try {
    uploading.value = true
    
    const formData = new FormData()
    formData.append('file', file.raw || file)
    
    const response = await knowledgeAPI.uploadDocument(selectedKB.value, formData)
    
    if (response.data?.success !== false) {
      ElMessage.success(`文件 ${file.name} 上传成功`)
      
      // 刷新文档列表
      await fetchDocuments()
      
      return true
    } else {
      throw new Error(response.data?.message || '上传失败')
    }
  } catch (error) {
    console.error('文件上传失败:', error)
    ElMessage.error(`文件上传失败: ${error.message}`)
    return false
  } finally {
    uploading.value = false
  }
}

// 辅助函数
const getDocumentType = (filename) => {
  if (!filename) return 'document'
  
  const ext = filename.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'md':
    case 'markdown':
      return 'markdown'
    case 'txt':
      return 'text'
    case 'pdf':
      return 'document'
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
      return 'image'
    case 'mp4':
    case 'avi':
    case 'mov':
      return 'video'
    default:
      return 'document'
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '未知'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatFileSize = (size) => {
  if (typeof size === 'string') return size
  if (!size || size === 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let fileSize = size
  
  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }
  
  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
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
  const ext = fileName.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'pdf': return 'Document'
    case 'txt': return 'DocumentCopy'
    case 'md': return 'Document'
    case 'docx': return 'Document'
    default: return 'Document'
  }
}

const beforeUpload = (file) => {
  const supportedFormats = knowledgeAPI.getSupportedFormats()
  const allFormats = [
    ...supportedFormats.documents,
    ...supportedFormats.code,
    ...supportedFormats.data
  ]
  
  const fileName = file.name.toLowerCase()
  const isSupported = allFormats.some(format => fileName.endsWith(format))
  
  if (!isSupported) {
    ElMessage.error(`不支持的文件格式。支持的格式: ${allFormats.join(', ')}`)
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  
  return true
}

const onUploadSuccess = async (response, file) => {
  ElMessage.success(`${file.name} 上传成功`)
  await fetchDocuments()
}

const onUploadError = (error, file) => {
  console.error('文件上传失败:', error)
  ElMessage.error(`${file.name} 上传失败`)
}

// 其他操作
const toggleDocSelection = (docId) => {
  const index = selectedDocs.value.indexOf(docId)
  if (index > -1) {
    selectedDocs.value.splice(index, 1)
  } else {
    selectedDocs.value.push(docId)
  }
}

const selectAll = () => {
  if (selectedDocs.value.length === filteredDocuments.value.length) {
    selectedDocs.value = []
  } else {
    selectedDocs.value = filteredDocuments.value.map(doc => doc.id)
  }
}

const exportKnowledgeBase = () => {
  if (!selectedKB.value) {
    ElMessage.warning('请先选择知识库')
    return
  }
  ElMessage.info('导出功能开发中')
}

const handleKBAction = async ({ action, kb }) => {
  switch (action) {
    case 'edit':
      editKBForm.value = { name: kb.name, description: kb.description }
      showEditKBDialog.value = true
      break
    case 'settings':
      showKBSettingsDialog.value = true
      break
    case 'duplicate':
      ElMessage.info('复制功能开发中')
      break
    case 'delete':
      await deleteKnowledgeBase(kb)
      break
  }
}

const deleteKnowledgeBase = async (kb) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库"${kb.name}"吗？此操作将删除所有相关文档且不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await knowledgeAPI.deleteKnowledgeBase(kb.id)
    ElMessage.success('知识库删除成功')
    
    // 如果删除的是当前选中的知识库，清空选择
    if (selectedKB.value === kb.id) {
      selectedKB.value = null
      documents.value = []
    }
    
    await fetchKnowledgeBases()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除知识库失败:', error)
      ElMessage.error('删除知识库失败')
    }
  }
}

const saveKBSettings = () => {
  ElMessage.success('Settings saved successfully!')
  showKBSettingsDialog.value = false
}

// 生命周期
onMounted(async () => {
  await fetchKnowledgeBases()
  await fetchStats()
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
  position: relative;
}

.kb-item:hover {
  background: var(--el-fill-color-light);
}

.kb-item:hover .kb-actions {
  opacity: 1;
}

.kb-item.active {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.kb-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
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
  --el-tabs-header-height: 48px;
}

.content-tabs :deep(.el-tabs__header) {
  margin: 0;
  border-bottom: 1px solid #3e3e42;
  background: #2d2d30;
  padding: 0 16px;
}

.content-tabs :deep(.el-tabs__nav-wrap) {
  padding: 8px 0;
}

.content-tabs :deep(.el-tabs__item) {
  height: 32px;
  line-height: 32px;
  padding: 0 16px;
  margin-right: 4px;
  border: 1px solid transparent;
  border-radius: 4px;
  color: #cccccc;
  background: transparent;
  font-size: 13px;
  font-weight: 400;
}

.content-tabs :deep(.el-tabs__item:hover) {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.content-tabs :deep(.el-tabs__item.is-active) {
  color: #ffffff;
  background: #007acc;
  border-color: #007acc;
}

.content-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.content-tabs :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

/* ========== 文档部分 ========== */
.documents-section {
  height: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.documents-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #3e3e42;
  background: #2d2d30;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  flex: 1;
}

.toolbar-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 300px;
}

.sort-select {
  width: 140px;
}

.documents-grid-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
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
  position: relative;
}

.document-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.document-card.selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.doc-checkbox {
  position: absolute;
  top: 8px;
  right: 8px;
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
  padding: 0;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.search-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #3e3e42;
  background: #2d2d30;
}

.search-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.search-title .el-icon {
  color: #007acc;
}

.search-description {
  font-size: 13px;
  color: #cccccc;
}

.search-input-area {
  padding: 16px 24px;
  border-bottom: 1px solid #3e3e42;
}

.search-input-box {
  width: 100%;
}

.search-input-box :deep(.el-input__inner) {
  height: 40px;
  font-size: 14px;
  background: #383838;
  border-color: #3e3e42;
  color: #cccccc;
}

.search-input-box :deep(.el-input__inner):focus {
  border-color: #007acc;
}

.search-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 24px;
  background: #252526;
  border-bottom: 1px solid #3e3e42;
  font-size: 12px;
  color: #cccccc;
}

.search-stats .el-icon {
  color: #007acc;
}

.results-title {
  padding: 16px 24px 12px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  background: #2d2d30;
  border-bottom: 1px solid #3e3e42;
}

.results-list {
  flex: 1;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  background: #2d2d30;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  padding: 16px;
  transition: all 0.2s ease;
}

.result-item:hover {
  border-color: #007acc;
  background: #383838;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.result-title-section {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.result-icon {
  color: #007acc;
  font-size: 14px;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
}

.result-meta-section {
  font-size: 12px;
}

.result-score {
  background: rgba(0, 122, 204, 0.15);
  color: #007acc;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 500;
}

.result-chunk-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #888888;
  margin-bottom: 12px;
}

.result-content {
  font-size: 13px;
  line-height: 1.5;
  color: #cccccc;
  margin-bottom: 12px;
  background: #383838;
  padding: 12px;
  border-radius: 4px;
  border-left: 3px solid #007acc;
}

.result-content :deep(mark) {
  background: rgba(255, 255, 0, 0.3);
  color: #ffff00;
  padding: 0 2px;
  border-radius: 2px;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.empty-results {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 48px;
  color: #666666;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  color: #cccccc;
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 13px;
  color: #888888;
}

/* ========== 上传部分 ========== */
.upload-section {
  padding: 0;
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.upload-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #3e3e42;
  background: #2d2d30;
}

.upload-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 4px;
}

.upload-title .el-icon {
  color: #007acc;
}

.upload-description {
  font-size: 13px;
  color: #cccccc;
}

.upload-area {
  padding: 24px;
  border-bottom: 1px solid #3e3e42;
}

.upload-dragger {
  width: 100%;
}

.upload-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: 160px;
  background: #383838;
  border: 2px dashed #666666;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.upload-dragger :deep(.el-upload-dragger:hover) {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.05);
}

.upload-dragger :deep(.el-upload-dragger.is-dragover) {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.upload-icon {
  font-size: 48px;
  color: #007acc;
  margin-bottom: 16px;
}

.upload-main-text {
  font-size: 16px;
  color: #ffffff;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.upload-hint {
  font-size: 13px;
  color: #cccccc;
  margin: 0;
}

.upload-options {
  padding: 20px 24px;
  border-bottom: 1px solid #3e3e42;
  background: #252526;
}

.options-title {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 16px;
}

.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.option-info {
  flex: 1;
}

.option-label {
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 2px;
}

.option-desc {
  font-size: 12px;
  color: #cccccc;
  line-height: 1.4;
}

.upload-queue {
  flex: 1;
  padding: 20px 24px;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.queue-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.queue-title .el-icon {
  color: #007acc;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #2d2d30;
  border: 1px solid #3e3e42;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.queue-item:hover {
  border-color: #007acc;
  background: #383838;
}

.file-icon {
  font-size: 16px;
  color: #007acc;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.file-size {
  color: #cccccc;
}

.file-status {
  padding: 1px 4px;
  border-radius: 2px;
  font-weight: 500;
}

.file-status.pending {
  background: rgba(255, 193, 7, 0.15);
  color: #ffc107;
}

.file-status.success {
  background: rgba(40, 167, 69, 0.15);
  color: #28a745;
}

.file-status.error {
  background: rgba(220, 53, 69, 0.15);
  color: #dc3545;
}

.upload-progress {
  width: 100px;
}

.file-actions {
  display: flex;
  align-items: center;
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

/* ========== 新功能样式 ========== */
.documents-list {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.doc-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-type-icon {
  color: var(--el-color-primary);
  font-size: 16px;
}

.stats-content {
  padding: 20px 0;
}

.chart-placeholder {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

/* ========== 深色主题适配 ========== */
.knowledge-base-page {
  background: #252526;
  color: #cccccc;
}

.page-header {
  background: #2d2d30;
  border-bottom-color: #3e3e42;
}

.knowledge-sidebar {
  background: #252526;
  border-right-color: #3e3e42;
}

.content-main {
  background: #1e1e1e;
}

.document-card {
  background: #2d2d30;
  border-color: #3e3e42;
  color: #cccccc;
}

.document-card:hover {
  border-color: #007acc;
  box-shadow: 0 2px 8px rgba(0, 122, 204, 0.2);
}

.document-card.selected {
  border-color: #007acc;
  background: rgba(0, 122, 204, 0.1);
}

.result-item {
  background: #2d2d30;
  border-color: #3e3e42;
  color: #cccccc;
}

.chunk-item {
  border-color: #3e3e42;
}

.chunk-header {
  background: #383838;
  border-bottom-color: #3e3e42;
}

.queue-item {
  background: #2d2d30;
  border-color: #3e3e42;
}

/* Element Plus 深色主题覆盖 */
:deep(.el-dialog) {
  background: #2d2d30;
  color: #cccccc;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #3e3e42;
}

:deep(.el-form-item__label) {
  color: #cccccc;
}

:deep(.el-input__inner) {
  background: #383838;
  border-color: #3e3e42;
  color: #cccccc;
}

:deep(.el-input__inner:focus) {
  border-color: #007acc;
}

:deep(.el-textarea__inner) {
  background: #383838;
  border-color: #3e3e42;
  color: #cccccc;
}

:deep(.el-select) {
  color: #cccccc;
}

:deep(.el-table) {
  background: #1e1e1e;
  color: #cccccc;
}

:deep(.el-table th) {
  background: #2d2d30;
  border-bottom-color: #3e3e42;
  color: #cccccc;
}

:deep(.el-table td) {
  border-bottom-color: #3e3e42;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #252526;
}

:deep(.el-table__body tr:hover td) {
  background: rgba(0, 122, 204, 0.1) !important;
}

:deep(.el-upload-dragger) {
  background: #2d2d30;
  border-color: #3e3e42;
  color: #cccccc;
}

:deep(.el-upload-dragger:hover) {
  border-color: #007acc;
}

:deep(.el-card) {
  background: #2d2d30;
  border-color: #3e3e42;
  color: #cccccc;
}

:deep(.el-descriptions__label) {
  color: #cccccc !important;
}

:deep(.el-descriptions__content) {
  color: #cccccc !important;
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