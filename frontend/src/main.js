import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'

console.log('Vue应用正在启动...')

// 添加全局错误处理
window.addEventListener('error', (event) => {
  console.error('全局错误:', event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise拒绝:', event.reason)
})

try {
  const app = createApp(App)
  const pinia = createPinia()

  console.log('创建Vue应用成功')

  // 注册Element Plus图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  console.log('注册Element Plus图标完成')

  app.use(pinia)
  console.log('注册Pinia完成')

  app.use(router)
  console.log('注册Router完成')

  app.use(ElementPlus, {
    locale: zhCn,
  })
  console.log('注册Element Plus完成')

  console.log('挂载应用到DOM...')
  app.mount('#app')
  console.log('Vue应用启动完成！')
} catch (error) {
  console.error('Vue应用启动失败:', error)
  // 在页面上显示错误信息
  document.body.innerHTML = `
    <div style="padding: 20px; font-family: Arial, sans-serif;">
      <h1>应用启动失败</h1>
      <p>错误信息: ${error.message}</p>
      <p>请检查浏览器控制台获取详细信息</p>
      <button onclick="location.reload()">重新加载</button>
    </div>
  `
} 