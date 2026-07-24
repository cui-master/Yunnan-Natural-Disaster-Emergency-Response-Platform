import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
<<<<<<< HEAD
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
=======
>>>>>>> feature-cui
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './style.css'
<<<<<<< HEAD
import './system-themes.css' // 角色差异化主题（覆盖 style.css 的主题段）
=======
>>>>>>> feature-cui

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
<<<<<<< HEAD

// 全局注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
=======
app.mount('#app')
>>>>>>> feature-cui
