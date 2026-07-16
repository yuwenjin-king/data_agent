import { create } from 'zustand'

export const useAppStore = create((set) => ({
  currentAgent: null,
  setCurrentAgent: (agent) => set({ currentAgent: agent }),

  currentSession: null,
  setCurrentSession: (session) => set({ currentSession: session }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
}))
