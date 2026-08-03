// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  app: {
    head: {
      title: 'Clean My Car · Ops',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Internal ops portal for Clean My Car' },
        { name: 'robots', content: 'noindex, nofollow' },
      ],
      htmlAttrs: { lang: 'en' },
    },
  },

  runtimeConfig: {
    // Server-only (future): proxy secrets, etc.
    // Public keys are exposed to the browser.
    public: {
      /** Backend origin, e.g. http://localhost:8000 */
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      /** Ops API prefix under the backend */
      opsApiPrefix: process.env.NUXT_PUBLIC_OPS_API_PREFIX || '/api/v1/ops',
    },
  },

  // SPA-friendly defaults for an authenticated internal tool; can enable SSR later.
  ssr: true,

  typescript: {
    strict: true,
    typeCheck: false, // enable via `npm run typecheck` once vue-tsc is added
  },
})
