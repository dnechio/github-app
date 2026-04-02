import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiFetch, setJwt } from '../services/api'

interface AuthStore {
  token: string | null
  login: (apiKey: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      token: null,
      login: async (apiKey: string) => {
        const { token } = await apiFetch<{ token: string; expires_in: number }>(
          '/auth/session',
          { method: 'POST', body: JSON.stringify({ api_key: apiKey }) },
        )
        setJwt(token)
        set({ token })
      },
      logout: () => {
        setJwt('')
        set({ token: null })
      },
    }),
    {
      name: 'auth',
      onRehydrateStorage: () => (state) => {
        if (state?.token) setJwt(state.token)
      },
    }
  )
)
