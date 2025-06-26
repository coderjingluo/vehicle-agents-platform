<template>
  <div class="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  // 初始化应用
});
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --primary-color: #4080ff;
  --secondary-color: #2b2d56;
  --bg-color: #111215;
  --bg-color-light: #1a1a1e;
  --bg-color-lighter: #1d1e22;
  --border-color: #2c2c2c;
  --border-color-light: #3e3e3e;
  --text-color: #ffffff;
  --text-color-secondary: #aaaaaa;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.app {
  height: 100%;
}

/* Override Element Plus theme */
:root {
  --el-color-primary: var(--primary-color);
}

/* Dark theme overrides for Element Plus */
.el-button--primary {
  --el-button-bg-color: var(--primary-color);
  --el-button-border-color: var(--primary-color);
  --el-button-hover-bg-color: #5090ff;
  --el-button-hover-border-color: #5090ff;
  --el-button-active-bg-color: #3070e0;
  --el-button-active-border-color: #3070e0;
}

.el-button--primary.is-plain {
  --el-button-bg-color: transparent;
  --el-button-border-color: var(--primary-color);
  --el-button-text-color: var(--primary-color);
  --el-button-hover-text-color: #fff;
  --el-button-hover-bg-color: var(--primary-color);
  --el-button-hover-border-color: var(--primary-color);
  --el-button-active-text-color: #fff;
}

.el-badge__content {
  background-color: #f56c6c;
}

.el-input__wrapper,
.el-textarea__wrapper {
  background-color: var(--bg-color-lighter) !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.el-input__wrapper.is-focus,
.el-textarea__wrapper.is-focus {
  box-shadow: 0 0 0 1px var(--primary-color) inset !important;
}

.el-input__inner,
.el-textarea__inner {
  color: var(--text-color) !important;
}

.el-dropdown-menu {
  background-color: var(--bg-color-light) !important;
  border-color: var(--border-color) !important;
}

.el-dropdown-menu__item {
  color: var(--text-color) !important;
}

.el-dropdown-menu__item:hover {
  background-color: var(--border-color) !important;
  color: var(--primary-color) !important;
}

.el-dialog {
  background-color: var(--bg-color-light) !important;
  border: 1px solid var(--border-color) !important;
}

.el-dialog__title,
.el-dialog__body,
.el-dialog__footer {
  color: var(--text-color) !important;
}

.el-dialog__header {
  border-bottom: 1px solid var(--border-color) !important;
}

.el-select {
  --el-select-input-color: var(--text-color) !important;
  --el-select-multiple-input-color: var(--text-color) !important;
  --el-select-input-focus-border-color: var(--primary-color) !important;
  --el-select-input-font-size: 14px !important;
}

.el-select .el-input__wrapper {
  background-color: var(--bg-color-lighter) !important;
}

.el-select-dropdown {
  background-color: var(--bg-color-light) !important;
  border: 1px solid var(--border-color) !important;
}

.el-select-dropdown__item {
  color: var(--text-color) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background-color: var(--border-color) !important;
}

.el-tabs__item {
  color: var(--text-color-secondary) !important;
}

.el-tabs__item.is-active {
  color: var(--primary-color) !important;
}

.el-tabs__active-bar {
  background-color: var(--primary-color) !important;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-color);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--border-color-light);
}

/* Markdown content styling */
.markdown-content h1, .markdown-content h2, .markdown-content h3,
.markdown-content h4, .markdown-content h5, .markdown-content h6 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-content h1 {
  font-size: 2em;
}

.markdown-content h2 {
  font-size: 1.5em;
}

.markdown-content h3 {
  font-size: 1.25em;
}

.markdown-content p, .markdown-content ul, .markdown-content ol {
  margin-bottom: 16px;
}

.markdown-content ul, .markdown-content ol {
  padding-left: 2em;
}

.markdown-content a {
  color: var(--primary-color);
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content code {
  padding: 0.2em 0.4em;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
}

.markdown-content pre {
  padding: 16px;
  overflow: auto;
  border-radius: 4px;
  background-color: #1e1e1e;
  margin-bottom: 16px;
}

.markdown-content pre code {
  padding: 0;
  background-color: transparent;
}

.markdown-content blockquote {
  padding: 0 16px;
  color: var(--text-color-secondary);
  border-left: 4px solid var(--border-color);
  margin-bottom: 16px;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.markdown-content table th, .markdown-content table td {
  padding: 8px;
  border: 1px solid var(--border-color);
}

.markdown-content table th {
  background-color: var(--bg-color-lighter);
  font-weight: 600;
}

/* Code syntax highlighting */
.hljs-keyword,
.hljs-selector-tag,
.hljs-literal,
.hljs-section,
.hljs-link {
  color: #569cd6;
}

.hljs-string,
.hljs-title,
.hljs-name,
.hljs-type,
.hljs-attribute,
.hljs-symbol,
.hljs-bullet,
.hljs-built_in,
.hljs-addition,
.hljs-variable,
.hljs-template-tag,
.hljs-template-variable {
  color: #9cdcfe;
}

.hljs-comment,
.hljs-quote,
.hljs-deletion,
.hljs-meta {
  color: #6a9955;
}

.hljs-keyword,
.hljs-selector-tag,
.hljs-literal,
.hljs-title,
.hljs-section,
.hljs-doctag,
.hljs-type,
.hljs-name,
.hljs-strong {
  font-weight: bold;
}

.hljs-emphasis {
  font-style: italic;
}
</style>
