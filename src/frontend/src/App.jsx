import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Contents from './pages/Contents'
import Crawler from './pages/Crawler'
import Analysis from './pages/Analysis'
import Publish from './pages/Publish'
import AI from './pages/AI'

function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="contents" element={<Contents />} />
          <Route path="crawler" element={<Crawler />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="publish" element={<Publish />} />
          <Route path="ai" element={<AI />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
