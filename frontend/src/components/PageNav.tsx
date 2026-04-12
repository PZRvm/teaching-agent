// frontend/src/components/PageNav.tsx
import styled from 'styled-components'
import type { ReactNode } from 'react'
import RoughButton from './RoughButton'

interface PageNavProps {
  /** 页面标题 */
  title: string
  /** 返回按钮回调，不传则不显示返回按钮 */
  onBack?: () => void
  /** 返回按钮文字，默认 "← 返回" */
  backLabel?: string
  /** 右侧插槽（badges、actions 等） */
  right?: ReactNode
}

export default function PageNav({ title, onBack, backLabel = '← 返回', right }: PageNavProps) {
  return (
    <Wrapper>
      <div className="nav-left">
        {onBack && (
          <RoughButton variant="outline" onClick={onBack} className="back-btn">
            {backLabel}
          </RoughButton>
        )}
        <h1 className="nav-title">{title}</h1>
      </div>
      {right && <div className="nav-right">{right}</div>}
    </Wrapper>
  )
}

const Wrapper = styled.nav`
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(250, 250, 250, 0.95);
  backdrop-filter: blur(4px);
  border-bottom: 2px solid #1a1a1a;
  box-shadow: 4px 4px 0px 0px #1a1a1a;

  .nav-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .nav-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #1a1c1c;
    margin: 0;
  }

  .nav-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .back-btn {
    padding: 6px 16px;
    font-size: 14px;
  }
`
