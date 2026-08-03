export default defineNuxtRouteMiddleware((to) => {
  // Tokens live in localStorage — enforce auth on the client only.
  if (import.meta.server) return

  const auth = useAuth()
  auth.hydrateFromStorage()

  const isLogin = to.path === '/login'

  if (isLogin) {
    if (auth.isLoggedIn.value) {
      return navigateTo('/')
    }
    return
  }

  if (!auth.isLoggedIn.value) {
    return navigateTo({ path: '/login', query: { next: to.fullPath } })
  }
})
