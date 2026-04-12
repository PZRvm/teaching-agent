// frontend/src/components/Footer.tsx
import styled from 'styled-components'

export default function Footer() {
  return (
    <Wrapper>
      <div className="footer-divider" aria-hidden="true">
        <div className="footer-divider-skew" />
      </div>
      <p className="footer-text">
        技术栈：<span className="footer-highlight">FastAPI</span> +{' '}
        <span className="footer-highlight">React</span> +{' '}
        <span className="footer-highlight">Qwen</span> +{' '}
        <span className="footer-highlight">SQLite</span>
      </p>
      <div className="footer-tags">
        <div className="footer-tag footer-tag-beta">
          BETA v0.8.2
        </div>
        <div className="footer-tag footer-tag-ai">
          AI SIMULATION
        </div>
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.footer`
  width: 100%;
  padding: 48px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;

  .footer-divider {
    width: 100%;
    max-width: 896px;
    height: 2px;
    background: #d4d4d4;
    position: relative;
    overflow: hidden;
  }

  .footer-divider-skew {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #d4d4d4;
    transform: scaleY(0.5) skewX(12deg);
  }

  .footer-text {
    font-size: 14px;
    font-weight: 500;
    color: #747688;
    letter-spacing: 0.5px;
    margin: 0;
  }

  .footer-highlight {
    color: #171717;
    font-weight: 700;
  }

  .footer-tags {
    display: flex;
    gap: 16px;
  }

  .footer-tag {
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
  }

  .footer-tag-beta {
    background: #fce4ec;
    transform: rotate(2deg);
  }

  .footer-tag-ai {
    background: #fff9c4;
    transform: rotate(-1deg);
  }
`
