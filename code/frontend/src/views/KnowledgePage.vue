<template>
  <div class="knowledge-page">
    <AppLayout>
      <div class="knowledge-container">
        <div class="sidebar">
          <div class="sidebar-header">
            <h2>知识库管理</h2>
            <el-button type="primary" size="small">
              <el-icon><Plus /></el-icon>
              创建知识库
            </el-button>
          </div>
          
          <div class="knowledge-bases">
            <div class="knowledge-base-item active">
              <div class="base-icon">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="base-info">
                <div class="base-name">车联网安全标准库</div>
                <div class="base-stats">文档: 24 | 更新: 2天前</div>
              </div>
            </div>
            
            <div class="knowledge-base-item">
              <div class="base-icon">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="base-info">
                <div class="base-name">安全测试用例库</div>
                <div class="base-stats">文档: 48 | 更新: 1周前</div>
              </div>
            </div>
            
            <div class="knowledge-base-item">
              <div class="base-icon">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="base-info">
                <div class="base-name">车联网威胁模型库</div>
                <div class="base-stats">文档: 18 | 更新: 2周前</div>
              </div>
            </div>
            
            <div class="knowledge-base-item">
              <div class="base-icon">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="base-info">
                <div class="base-name">测试报告模板库</div>
                <div class="base-stats">文档: 12 | 更新: 3周前</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="main-content">
          <div class="tabs-container">
            <div class="tabs">
              <div class="tab active">
                <el-icon><Document /></el-icon>
                文档管理
              </div>
              <div class="tab">
                <el-icon><Search /></el-icon>
                知识检索
              </div>
              <div class="tab">
                <el-icon><Upload /></el-icon>
                上传管理
              </div>
            </div>
            
            <div class="search-box">
              <el-input
                placeholder="搜索文档..."
                prefix-icon="Search"
              />
            </div>
          </div>
          
          <div class="documents-container">
            <div class="filter-bar">
              <div class="filter-by">
                <span>筛选：</span>
                <el-select v-model="fileType" placeholder="文件类型">
                  <el-option label="全部" value="all" />
                  <el-option label="文档" value="doc" />
                  <el-option label="PDF" value="pdf" />
                  <el-option label="表格" value="excel" />
                </el-select>
              </div>
              
              <div class="sort-by">
                <span>排序：</span>
                <el-select v-model="sortBy" placeholder="排序方式">
                  <el-option label="上传时间" value="date" />
                  <el-option label="文件名" value="name" />
                  <el-option label="文件大小" value="size" />
                </el-select>
              </div>
            </div>
            
            <div class="documents-list">
              <div class="document-item" v-for="doc in documents" :key="doc.id">
                <div class="doc-icon" :class="doc.type">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="doc-info">
                  <div class="doc-name">{{ doc.name }}</div>
                  <div class="doc-meta">{{ doc.size }} | {{ doc.date }}</div>
                </div>
                <div class="doc-actions">
                  <el-button type="text" circle>
                    <el-icon><View /></el-icon>
                  </el-button>
                  <el-button type="text" circle>
                    <el-icon><Download /></el-icon>
                  </el-button>
                  <el-button type="text" circle>
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              
              <div class="upload-box">
                <div class="upload-icon">
                  <el-icon><Upload /></el-icon>
                </div>
                <div class="upload-text">
                  <div>拖拽文件至此处，或 <span class="upload-link">点击上传</span></div>
                  <div class="upload-desc">支持 .txt, .md, .pdf, .docx 等格式</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Plus, Folder, Document, Search, Upload, View, Download, Delete } from '@element-plus/icons-vue';
import AppLayout from '@/components/Layout/AppLayout.vue';

const fileType = ref('all');
const sortBy = ref('date');

const documents = [
  {
    id: 1,
    name: 'ISO 21434 - 车辆网络安全标准概述.pdf',
    type: 'pdf',
    size: '1.2 MB',
    date: '2023-06-15'
  },
  {
    id: 2,
    name: 'TARA分析方法与实践指南.docx',
    type: 'doc',
    size: '856 KB',
    date: '2023-06-10'
  },
  {
    id: 3,
    name: 'GB/T 38278 智能网联汽车网络安全技术要求.pdf',
    type: 'pdf',
    size: '2.1 MB',
    date: '2023-06-05'
  },
  {
    id: 4,
    name: '车联网安全测试用例集 - V1.0.xlsx',
    type: 'excel',
    size: '1.5 MB',
    date: '2023-05-28'
  },
  {
    id: 5,
    name: '车联网网络安全风险评估模板.docx',
    type: 'doc',
    size: '720 KB',
    date: '2023-05-20'
  }
];
</script>

<style scoped>
.knowledge-page {
  height: 100%;
}

.knowledge-container {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 280px;
  background-color: #1a1a1e;
  border-right: 1px solid #2c2c2c;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #2c2c2c;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-bases {
  padding: 15px;
  overflow-y: auto;
  flex: 1;
}

.knowledge-base-item {
  display: flex;
  padding: 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: background-color 0.2s;
}

.knowledge-base-item:hover {
  background-color: #2c2c2c;
}

.knowledge-base-item.active {
  background-color: #2b2d56;
}

.base-icon {
  margin-right: 12px;
  font-size: 20px;
  color: #aaa;
}

.knowledge-base-item.active .base-icon {
  color: #4080ff;
}

.base-info {
  flex: 1;
}

.base-name {
  font-size: 14px;
  margin-bottom: 4px;
}

.base-stats {
  font-size: 12px;
  color: #aaa;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #111215;
}

.tabs-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  border-bottom: 1px solid #2c2c2c;
}

.tabs {
  display: flex;
}

.tab {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  margin-right: 10px;
  border-radius: 4px;
  cursor: pointer;
}

.tab.active {
  background-color: #2c2c2c;
  color: #4080ff;
}

.tab .el-icon {
  margin-right: 8px;
}

.search-box {
  width: 250px;
}

.search-box :deep(.el-input__wrapper) {
  background-color: #2c2c2c;
  box-shadow: none;
  border-radius: 4px;
}

.search-box :deep(.el-input__inner) {
  color: #fff;
}

.documents-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.filter-by, .sort-by {
  display: flex;
  align-items: center;
}

.filter-by span, .sort-by span {
  margin-right: 10px;
  color: #aaa;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background-color: #1a1a1e;
  border-radius: 4px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.document-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.doc-icon {
  width: 40px;
  height: 40px;
  background-color: #2c2c2c;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 20px;
}

.doc-icon.pdf {
  color: #e74c3c;
}

.doc-icon.doc {
  color: #3498db;
}

.doc-icon.excel {
  color: #2ecc71;
}

.doc-info {
  flex: 1;
}

.doc-name {
  font-size: 14px;
  margin-bottom: 5px;
}

.doc-meta {
  font-size: 12px;
  color: #aaa;
}

.doc-actions {
  display: flex;
  gap: 5px;
}

.upload-box {
  display: flex;
  align-items: center;
  padding: 25px;
  background-color: #1a1a1e;
  border: 2px dashed #2c2c2c;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 20px;
  transition: border-color 0.2s;
}

.upload-box:hover {
  border-color: #4080ff;
}

.upload-icon {
  font-size: 24px;
  margin-right: 20px;
  color: #aaa;
}

.upload-text {
  color: #aaa;
}

.upload-link {
  color: #4080ff;
  cursor: pointer;
}

.upload-desc {
  font-size: 12px;
  margin-top: 5px;
}
</style> 