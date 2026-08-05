import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

/**
 * Register Ant Design Vue globally so CSS-in-JS styles mount with components.
 * Ops UI runs as SPA (ssr: false) so style injection works in the browser.
 */
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(Antd)
})
