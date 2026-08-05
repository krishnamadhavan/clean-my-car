// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  // SPA: Ant Design Vue 4 CSS-in-JS injects reliably client-side.
  // Ops is an internal portal; SSR is not required.
  ssr: false,

  css: ['ant-design-vue/dist/reset.css', '~/assets/css/main.css'],

  app: {
    head: {
      title: 'Clean My Car · Ops',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Internal ops portal for Clean My Car' },
        { name: 'robots', content: 'noindex, nofollow' },
        { name: 'theme-color', content: '#4B49AC' },
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/logo-mark.svg' },
        { rel: 'icon', type: 'image/png', sizes: '32x32', href: '/favicon-32.png' },
        { rel: 'apple-touch-icon', href: '/logo.png' },
      ],
      htmlAttrs: { lang: 'en' },
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      opsApiPrefix: process.env.NUXT_PUBLIC_OPS_API_PREFIX || '/api/v1/ops',
    },
  },

  build: {
    transpile: ['ant-design-vue', '@ant-design/icons-vue', /dayjs/],
  },

  vite: {
    optimizeDeps: {
      include: [
        'ant-design-vue',
        '@ant-design/icons-vue',
        'dayjs',
        'dayjs/plugin/advancedFormat',
        'dayjs/plugin/customParseFormat',
        'dayjs/plugin/localeData',
        'dayjs/plugin/weekday',
        'dayjs/plugin/weekOfYear',
        'dayjs/plugin/weekYear',
        'dayjs/plugin/quarterOfYear',
      ],
      needsInterop: [
        'dayjs',
        'dayjs/plugin/advancedFormat',
        'dayjs/plugin/customParseFormat',
        'dayjs/plugin/localeData',
        'dayjs/plugin/weekday',
        'dayjs/plugin/weekOfYear',
        'dayjs/plugin/weekYear',
        'dayjs/plugin/quarterOfYear',
      ],
    },
    resolve: {
      dedupe: ['dayjs'],
    },
  },

  typescript: {
    strict: true,
    typeCheck: false,
  },
})
