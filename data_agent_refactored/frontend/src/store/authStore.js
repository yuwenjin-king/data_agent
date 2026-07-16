import { create } from 'zustand'

export const TOKEN_KEY = 'data_agent_token'

export const useAuthStore = create((set) => ({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: null,
  authEnabled: null, // unknown until /auth/status is fetched

  setToken: (token) => {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
    set({ token })
  },
  setUser: (user) => set({ user }),
  setAuthEnabled: (authEnabled) => set({ authEnabled }),
  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    set({ token: null, user: null })
  },
}))
