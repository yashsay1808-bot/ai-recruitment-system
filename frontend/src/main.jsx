import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import AuthCard from './components/AuthCard.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'

// Strict gate: nothing from the app (sidebar, header, data) is rendered until a user is signed in.
function Root() {
  const { isAuthenticated, status } = useAuth()
  if (status === 'loading') return <div className="min-h-screen bg-slate-50" aria-busy="true" />
  return isAuthenticated ? <App /> : <AuthCard />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <Root />
    </AuthProvider>
  </StrictMode>,
)
