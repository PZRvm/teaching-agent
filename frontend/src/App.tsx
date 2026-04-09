import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import ObservationConfig from './views/ObservationConfig'
import ObservationView from './views/ObservationView'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/observation/config" element={<ObservationConfig />} />
      <Route path="/observation/session/:sessionId" element={<ObservationView />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
