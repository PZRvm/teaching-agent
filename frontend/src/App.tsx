import { useState } from 'react'
import styled from 'styled-components'

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <Wrapper>
      <div className="center">
        <div className="hero">
          <img src="/vite.svg" alt="Vite logo" width="100" />
        </div>
        <h1 className="title">教学智能体</h1>
        <p className="description">基于 React + FastAPI + LangChain</p>
        <button className="counter" onClick={() => setCount(count + 1)}>
          Count is {count}
        </button>
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  .center {
    text-align: center;

    .hero {
      margin-bottom: 20px;
    }

    .title {
      font-size: 32px;
      color: #333;
      margin-bottom: 10px;
    }

    .description {
      font-size: 16px;
      color: #666;
      margin-bottom: 20px;
    }

    .counter {
      padding: 10px 20px;
      font-size: 16px;
      background-color: #646cff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: #535bf2;
      }
    }
  }
`
