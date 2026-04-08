import styled from 'styled-components'
import { useNavigate } from 'react-router-dom'
import RoughButton from '../components/RoughButton'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Wrapper>
      <main className="main">
        <div className="sketch-box">
          <span className="code" aria-label="404">404</span>
          <svg
            className="strike"
            viewBox="0 0 200 20"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <path
              d="M0 10 Q 50 2, 100 12 T 200 8"
              fill="transparent"
              stroke="currentColor"
              strokeLinecap="round"
              strokeWidth="4"
            />
          </svg>
        </div>
        <h1 className="title">页面未找到</h1>
        <p className="description">
          看起来你迷路了。这个页面可能已经被移动、删除，或者从未存在过。
        </p>
        <RoughButton variant="primary" onClick={() => navigate('/')}>
          返回首页 →
        </RoughButton>
      </main>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  width: 100%;
  background: #f9f9f9;
  color: #1a1c1c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Plus Jakarta Sans', system-ui, -apple-system, BlinkMacSystemFont,
    sans-serif;

  .main {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    padding: 24px;
    text-align: center;
  }

  .sketch-box {
    position: relative;
    display: inline-block;
  }

  .code {
    font-size: 120px;
    font-weight: 800;
    color: #d4d4d4;
    line-height: 1;
    user-select: none;
  }

  .strike {
    position: absolute;
    top: 50%;
    left: -8px;
    right: -8px;
    width: calc(100% + 16px);
    height: 20px;
    color: #b7102a;
    transform: translateY(-50%) rotate(-1deg);
  }

  .title {
    font-size: 32px;
    font-weight: 800;
    margin: 0;
    color: #1a1c1c;
  }

  .description {
    font-size: 18px;
    color: #525252;
    max-width: 400px;
    line-height: 1.625;
    margin: 0;
  }
`
