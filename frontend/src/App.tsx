import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
