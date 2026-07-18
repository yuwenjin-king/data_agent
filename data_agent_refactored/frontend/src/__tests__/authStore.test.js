import { describe, it, expect, beforeEach } from 'vitest'

import { TOKEN_KEY, useAuthStore } from '../store/authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ token: null, user: null, authEnabled: null })
  })

  it('persists token to localStorage via setToken', () => {
    useAuthStore.getState().setToken('abc123')
    expect(localStorage.getItem(TOKEN_KEY)).toBe('abc123')
    expect(useAuthStore.getState().token).toBe('abc123')
  })

  it('clears token from store and localStorage on logout', () => {
    useAuthStore.getState().setToken('abc123')
    useAuthStore.getState().logout()
    expect(useAuthStore.getState().token).toBeNull()
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
  })

  it('setToken(null) removes the stored token', () => {
    useAuthStore.getState().setToken('abc123')
    useAuthStore.getState().setToken(null)
    expect(localStorage.getItem(TOKEN_KEY)).toBeNull()
    expect(useAuthStore.getState().token).toBeNull()
  })
})
