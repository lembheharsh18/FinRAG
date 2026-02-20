import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ForgotPassword from './pages/ForgotPassword'
import Dashboard from './pages/Dashboard'
import StockDashboard from './pages/StockDashboard'
import AnalyticsPage from './pages/AnalyticsPage'
import ComparePage from './pages/ComparePage'
import AlertsPage from './pages/AlertsPage'
import LandingPage from './pages/LandingPage'
import EvaluationPage from './pages/EvaluationPage'
import ErrorBoundary from './components/ErrorBoundary'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Public route wrapper (redirects to dashboard if logged in)
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    )
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

// Landing route: shows landing page for guests, redirects to dashboard for logged-in users
function LandingRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="thinking-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    )
  }

  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return <LandingPage />
}

function App() {
  return (
    <ErrorBoundary>
    <Routes>
      {/* Public routes */}
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } 
      />
      <Route 
        path="/signup" 
        element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        } 
      />
      <Route 
        path="/forgot-password" 
        element={
          <PublicRoute>
            <ForgotPassword />
          </PublicRoute>
        } 
      />

      {/* Protected routes */}
      <Route 
        path="/dashboard/stocks" 
        element={
          <ProtectedRoute>
            <StockDashboard />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/dashboard/analytics" 
        element={
          <ProtectedRoute>
            <AnalyticsPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/dashboard/compare" 
        element={
          <ProtectedRoute>
            <ComparePage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/dashboard/alerts" 
        element={
          <ProtectedRoute>
            <AlertsPage />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/dashboard/*" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />

      {/* Evaluation route */}
      <Route 
        path="/dashboard/evaluate" 
        element={
          <ProtectedRoute>
            <EvaluationPage />
          </ProtectedRoute>
        } 
      />

      {/* Landing page for unauthenticated users */}
      <Route path="/" element={<LandingRoute />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </ErrorBoundary>
  )
}

export default App
