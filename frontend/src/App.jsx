import { ClerkProvider, SignIn, SignedIn, SignedOut, UserButton } from '@clerk/clerk-react'
import Dashboard from './components/Dashboard'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

function App() {
  // If Clerk key is not configured, show the dashboard without auth
  // (backend also falls through when CLERK_SECRET_KEY is empty)
  if (!PUBLISHABLE_KEY) {
    return (
      <div className="app">
        <header className="header">
          <h1>FalconConnect</h1>
          <span className="badge badge-warn">Auth not configured</span>
        </header>
        <Dashboard />
      </div>
    )
  }

  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
      <SignedOut>
        <div className="auth-screen">
          <div className="auth-card">
            <h1>FalconConnect</h1>
            <p className="subtitle">Internal Dashboard</p>
            <SignIn />
          </div>
        </div>
      </SignedOut>
      <SignedIn>
        <div className="app">
          <header className="header">
            <h1>FalconConnect</h1>
            <UserButton />
          </header>
          <Dashboard />
        </div>
      </SignedIn>
    </ClerkProvider>
  )
}

export default App
