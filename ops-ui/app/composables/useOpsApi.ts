import type { ApiErrorBody, OpsAccessToken, OpsTokenPair } from '~/types/ops'

export class OpsApiError extends Error {
  status: number
  code: string
  body: ApiErrorBody

  constructor(status: number, body: ApiErrorBody) {
    super(body.message || body.code || `Request failed (${status})`)
    this.name = 'OpsApiError'
    this.status = status
    this.code = body.code || 'request_failed'
    this.body = body
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

interface OpsFetchOptions {
  method?: HttpMethod
  body?: unknown
  query?: Record<string, string | number | boolean | null | undefined>
  auth?: boolean
  /** Skip one refresh retry (internal). */
  _retried?: boolean
}

function buildQuery(query?: OpsFetchOptions['query']): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue
    params.set(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

export function useOpsApi() {
  const config = useRuntimeConfig()
  const auth = useAuth()

  function baseUrl(path: string): string {
    const root = String(config.public.apiBase).replace(/\/$/, '')
    const prefix = String(config.public.opsApiPrefix).replace(/\/$/, '')
    const p = path.startsWith('/') ? path : `/${path}`
    return `${root}${prefix}${p}`
  }

  async function refreshAccess(): Promise<boolean> {
    if (!auth.refreshToken.value) return false
    try {
      const data = await $fetch<OpsAccessToken>(baseUrl('/auth/token/refresh'), {
        method: 'POST',
        body: { refresh_token: auth.refreshToken.value },
      })
      auth.updateTokens(data.access_token, data.refresh_token)
      return true
    } catch {
      auth.clearSession()
      return false
    }
  }

  async function opsFetch<T>(path: string, options: OpsFetchOptions = {}): Promise<T> {
    auth.hydrateFromStorage()
    const method = options.method || 'GET'
    const headers: Record<string, string> = {
      Accept: 'application/json',
    }
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json'
    }
    if (options.auth !== false && auth.accessToken.value) {
      headers.Authorization = `Bearer ${auth.accessToken.value}`
    }

    try {
      return await $fetch<T>(baseUrl(path) + buildQuery(options.query), {
        method,
        body: options.body as BodyInit | Record<string, unknown> | null | undefined,
        headers,
      })
    } catch (err: unknown) {
      const e = err as {
        statusCode?: number
        status?: number
        data?: ApiErrorBody
        response?: { status?: number; _data?: ApiErrorBody }
      }
      const status = e.statusCode || e.status || e.response?.status || 0
      const body: ApiErrorBody = e.data || e.response?._data || {}

      if (status === 401 && options.auth !== false && !options._retried) {
        const ok = await refreshAccess()
        if (ok) {
          return opsFetch<T>(path, { ...options, _retried: true })
        }
        if (import.meta.client) {
          await navigateTo('/login')
        }
      }

      throw new OpsApiError(status, {
        code: body.code,
        message: body.message || (typeof body.detail === 'string' ? body.detail : undefined),
        detail: body.detail,
      })
    }
  }

  async function login(email: string, password: string): Promise<OpsTokenPair> {
    const pair = await opsFetch<OpsTokenPair>('/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    })
    auth.setSession(pair)
    return pair
  }

  async function logout(): Promise<void> {
    const refresh = auth.refreshToken.value
    try {
      if (refresh) {
        await opsFetch('/auth/logout', {
          method: 'POST',
          body: { refresh_token: refresh },
          auth: false,
        })
      }
    } catch {
      /* still clear local session */
    } finally {
      auth.clearSession()
    }
  }

  return { opsFetch, login, logout, baseUrl }
}
