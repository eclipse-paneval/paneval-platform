import 'element-plus/dist/index.css'
import '@/styles/index.css'
import { createApp } from 'vue'
import App from '@/App.vue'
import { installProviders } from '@/app/providers'

const app = createApp(App)

installProviders(app)

app.mount('#app')
