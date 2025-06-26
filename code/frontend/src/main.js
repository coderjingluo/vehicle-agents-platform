import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'
import App from './App.vue'
import { setupStore } from './stores'
import 'highlight.js/styles/atom-one-dark.css'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import xml from 'highlight.js/lib/languages/xml'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'

// Register highlight.js languages
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)

const app = createApp(App)

// Register all Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.use(createPinia())

// Setup pinia store
setupStore()

// Use plugins
app.use(router)
app.use(ElementPlus)

// Custom directives
app.directive('highlight', {
  mounted(el) {
    const blocks = el.querySelectorAll('pre code')
    blocks.forEach(block => {
      hljs.highlightElement(block)
    })
  },
  updated(el) {
    const blocks = el.querySelectorAll('pre code')
    blocks.forEach(block => {
      hljs.highlightElement(block)
    })
  }
})

app.mount('#app')
