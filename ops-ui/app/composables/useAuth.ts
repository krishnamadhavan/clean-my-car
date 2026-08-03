import type { OpsOperator, OpsTokenPair } from '~/types/ops'

const ACCESS_KEY = 'cmc_ops_access'
const REFRESH_KEY = 'cmc_ops_refresh'
const OPERATOR_KEY = 'cmc_ops_operator'

function readStorage(key: string): string | null {
  if (!import.meta.client) return null
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStorage(key: string, value: string | null) {
  if (!import.meta.client) return
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch {
    /* ignore quota / private mode */
  }
}

export function useAuth() {
  const accessToken = useState<string | null>('ops-access', () => null)
  const refreshToken = useState<string | null>('ops-refresh', () => null)
  const operator = useState<OpsOperator | null>('ops-operator', () => null)
  const hydrated = useState<boolean>('ops-auth-hydrated', () => false)

  const isLoggedIn = computed(() => Boolean(accessToken.value))

  function hydrateFromStorage() {
    if (!import.meta.client || hydrated.value) return
    accessToken.value = readStorage(ACCESS_KEY)
    refreshToken.value = readStorage(REFRESH_KEY)
    const raw = readStorage(OPERATOR_KEY)
    if (raw) {
      try {
        operator.value = JSON.parse(raw) as OpsOperator
      } catch {
        operator.value = null
      }
    }
    hydrated.value = true
  }

  function setSession(pair: OpsTokenPair) {
    accessToken.value = pair.access_token
    refreshToken.value = pair.refresh_token
    operator.value = pair.operator
    writeStorage(ACCESS_KEY, pair.access_token)
    writeStorage(REFRESH_KEY, pair.refresh_token)
    writeStorage(OPERATOR_KEY, JSON.stringify(pair.operator))
  }

  function updateTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    writeStorage(ACCESS_KEY, access)
    writeStorage(REFRESH_KEY, refresh)
  }

  function clearSession() {
    accessToken.value = null
    refreshToken.value = null
    operator.value = null
    writeStorage(ACCESS_KEY, null)
    writeStorage(REFRESH_KEY, null)
    writeStorage(OPERATOR_KEY, null)
  }

  return {
    accessToken,
    refreshToken,
    operator,
    isLoggedIn,
    hydrated,
    hydrateFromStorage,
    setSession,
    updateTokens,
    clearSession,
  }
}
