import styled from 'styled-components'
import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'

export default function App() {
  return (
    <Wrapper>
      <Routes>
        <Route path="/" element={<LandingPage />} />
      </Routes>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  background: #f9f9f9;
  color-scheme: light;
`
