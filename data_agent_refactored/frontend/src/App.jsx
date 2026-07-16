import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import AgentDetail from './pages/AgentDetail'
import Chat from './pages/Chat'
import Settings from './pages/Settings'
import Login from './pages/Login'
import { authService } from './services'
import { useAuthStore } from './store/authStore'

/** Fetch /auth/status once; if the backend requires auth and there's no
 *  token, redirect to /login. When auth is disabled, render through. */
function AuthGate({ children }) {
  const token = useAuthStore((s) => s.token)
  const authEnabled = useAuthStore((s) => s.authEnabled)
  const setAuthEnabled = useAuthStore((s) => s.setAuthEnabled)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    authService
      .status()
      .then((res) => setAuthEnabled(res.data.data.auth_enabled))
      .catch(() => setAuthEnabled(false))
      .finally(() => setChecked(true))
  }, [setAuthEnabled])

  if (!checked) return null
  if (authEnabled && !token) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <AuthGate>
              <AppLayout />
            </AuthGate>
          }
        >
          <Route index element={<Dashboard />} />
          <Route path="agents" element={<Agents />} />
          <Route path="agents/:id" element={<AgentDetail />} />
          <Route path="chat/:agentId" element={<Chat />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
