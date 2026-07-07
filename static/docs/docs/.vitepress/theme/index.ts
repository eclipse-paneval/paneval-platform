import DefaultTheme from 'vitepress/theme'
import mediumZoom from 'medium-zoom/dist/pure'
import { nextTick, onMounted, watch } from 'vue'
import { useRoute } from 'vitepress'
import './custom.css'
import 'medium-zoom/dist/style.css'

export default {
  extends: DefaultTheme,
  setup() {
    const route = useRoute()

    onMounted(() => {
      const zoom = mediumZoom({
        background: 'var(--vp-c-bg)',
        margin: 24,
        scrollOffset: 0
      })

      const attachZoom = () => {
        zoom.detach()
        zoom.attach('.vp-doc img:not(.no-zoom)')
      }

      nextTick(attachZoom)
      watch(
        () => route.path,
        () => nextTick(attachZoom)
      )
    })
  }
}
