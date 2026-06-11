import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import ObservationConfig from './views/ObservationConfig'
import ObservationView from './views/ObservationView'
import SessionHistory from './views/SessionHistory'
import SessionDetail from './views/SessionDetail'
import AnalyticsDashboard from './views/AnalyticsDashboard'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/history" element={<SessionHistory />} />
      <Route path="/history/:sessionId" element={<SessionDetail />} />
      <Route path="/observation/config" element={<ObservationConfig />} />
      <Route path="/observation/session/:sessionId" element={<ObservationView />} />
      <Route path="/analytics" element={<AnalyticsDashboard />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
