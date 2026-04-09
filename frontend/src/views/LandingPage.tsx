import styled from 'styled-components'
import { useNavigate } from 'react-router-dom'
import RoughButton from '../components/RoughButton'
import Footer from '../components/Footer'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <Wrapper>
      {/* 背景装饰元素 */}
      <div className="bg-decoration-left" aria-hidden="true" />
      <div className="bg-decoration-right" aria-hidden="true" />

      {/* 导航栏 */}
      <nav className="top-nav">
        <div className="top-nav-left">
          <span className="brand-name">SimuSketch</span>
          <div className="brand-divider" aria-hidden="true" />
          <span className="brand-subtitle">教学智能体</span>
        </div>
        <div className="top-nav-right">
          <button className="nav-icon" aria-label="教学历史" onClick={() => navigate('/history')}>
            <span className="material-symbols-outlined">history</span>
          </button>
          <button className="nav-icon" aria-label="设置" disabled>
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="nav-avatar sketch-shadow" role="img" aria-label="用户头像" />
        </div>
      </nav>

      {/* 主内容区域 */}
      <main className="main">
        {/* Hero Section */}
        <header className="hero">
          <h1 className="hero-title">
            教学智能体
            <svg
              className="hero-underline"
              viewBox="0 0 100 20"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path
                d="M0 10 Q 25 0, 50 10 T 100 10"
                fill="transparent"
                stroke="currentColor"
                strokeLinecap="round"
                strokeWidth="4"
              />
            </svg>
          </h1>
          <p className="hero-subtitle">
            多Agent教学模拟系统
            <svg
              className="hero-subtitle-line"
              viewBox="0 0 100 10"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path
                d="M0 5 L 100 5"
                fill="transparent"
                stroke="currentColor"
                strokeDasharray="5 5"
                strokeWidth="2"
              />
            </svg>
          </p>
        </header>

        {/* 卡片网格 */}
        <section className="mode-grid" aria-label="模式选择">
          {/* 观察模式卡片 */}
          <article className="mode-card observation" aria-label="观察模式">
            <div className="tape tape-left" aria-hidden="true" />
            <div className="card-content">
              <span className="card-icon material-symbols-outlined" aria-hidden="true">
                visibility
              </span>
              <h2 className="card-title">观察模式</h2>
              <p className="card-description">
                进入旁观席位，观察多个AI智能体在模拟课堂中的实时互动、逻辑推演与反馈循环。深入剖析Agent间的协同机制与知识传递路径。
              </p>
              <RoughButton variant="primary" className="card-button" onClick={() => navigate('/observation/config')}>
                开始观察 →
              </RoughButton>
            </div>
            <div
              className="card-decoration card-decoration-observation"
              aria-hidden="true"
            >
              <span className="material-symbols-outlined">query_stats</span>
            </div>
          </article>

          {/* 教师模式卡片 */}
          <article className="mode-card teacher" aria-label="教师模式">
            <div className="tape tape-right" aria-hidden="true" />
            <div className="star-decoration" aria-hidden="true">
              <span className="material-symbols-outlined star-icon">grade</span>
            </div>
            <div className="card-content">
              <span className="card-icon material-symbols-outlined" aria-hidden="true">
                school
              </span>
              <h2 className="card-title">教师模式</h2>
              <p className="card-description">
                扮演引导者角色，直接参与教学模拟。设定教学目标，干预Agent学习进程，并在高保真模拟环境中验证您的教学策略与课程设计。
              </p>
              <RoughButton variant="teacher" className="card-button" onClick={() => navigate('/teacher/config')}>
                开始教学 →
              </RoughButton>
            </div>
            <div
              className="card-decoration card-decoration-teacher"
              aria-hidden="true"
            >
              <span className="material-symbols-outlined">school</span>
            </div>
          </article>
        </section>
      </main>

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  width: 100%;
  background: #f9f9f9;
  color: #1a1c1c;
  color-scheme: light;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, BlinkMacSystemFont,
    sans-serif;
  position: relative;
  overflow: hidden;

  /* ===== 背景装饰 ===== */
  .bg-decoration-left {
    position: fixed;
    top: 10%;
    left: -5%;
    width: 200px;
    height: 200px;
    background: rgba(46, 92, 255, 0.03);
    border-radius: 50%;
    filter: blur(40px);
    pointer-events: none;
    z-index: 0;
  }

  .bg-decoration-right {
    position: fixed;
    bottom: 10%;
    right: -5%;
    width: 250px;
    height: 250px;
    background: rgba(39, 224, 169, 0.03);
    border-radius: 50%;
    filter: blur(50px);
    pointer-events: none;
    z-index: 0;
  }

  /* ===== 导航栏 ===== */
  .top-nav {
    position: sticky;
    top: 0;
    z-index: 50;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #fafafa;
    border-bottom: 2px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
  }

  .top-nav-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .brand-name {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 800;
    font-size: 24px;
    color: #1a1c1c;
    text-decoration: underline wavy #2e5cff;
    text-underline-offset: 4px;
  }

  .brand-divider {
    width: 2px;
    height: 24px;
    background: #1a1a1a;
    transform: rotate(12deg);
  }

  .brand-subtitle {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-weight: 700;
    font-size: 18px;
    color: #1a1c1c;
    letter-spacing: -0.5px;
  }

  .top-nav-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .nav-icon {
    background: transparent;
    border: none;
    cursor: pointer;
    color: #1a1c1c;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    transition: transform 0.2s ease;

    &:focus-visible {
      outline: 2px dashed #1a1a1a;
      outline-offset: 2px;
    }

    &:hover {
      transform: scale(1.1);
    }
  }

  .nav-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 2px solid #1a1a1a;
    overflow: hidden;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    background: #e2e2e2;
  }

  .sketch-shadow {
    box-shadow: 4px 4px 0px 0px #1a1a1a;
  }

  /* ===== 主内容区 ===== */
  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 64px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  /* ===== Hero Section ===== */
  .hero {
    text-align: center;
    margin-bottom: 80px;
  }

  .hero-title {
    position: relative;
    display: inline-block;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 16px;
    color: #1a1c1c;
  }

  .hero-underline {
    position: absolute;
    bottom: -16px;
    left: 0;
    width: 100%;
    height: 16px;
    color: #2e5cff;
  }

  .hero-subtitle {
    position: relative;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    color: #525252;
    margin-top: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .hero-subtitle-line {
    width: 192px;
    height: 8px;
    color: #b7102a;
    margin-top: 8px;
  }

  /* ===== 卡片网格 ===== */
  .mode-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 48px;
    width: 100%;
    max-width: 1024px;

    @media (min-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* ===== 卡片通用 ===== */
  .mode-card {
    position: relative;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 40px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
      box-shadow: 8px 8px 0px 0px #1a1a1a;
      transform: translate(-4px, -4px);
    }
  }

  .mode-card.observation {
    background: #e3f2fd;
    border-color: #2e5cff;
    transform: rotate(-0.5deg);

    &:hover {
      transform: translate(-4px, -4px) rotate(-0.5deg);
    }
  }

  .mode-card.teacher {
    background: #e8f5e9;
    border-color: #007d5c;
    transform: rotate(1deg);

    &:hover {
      transform: translate(-4px, -4px) rotate(1deg);
    }
  }

  /* ===== 胶带 ===== */
  .tape {
    position: absolute;
    top: -16px;
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    border-left: 1px solid rgba(200, 200, 200, 0.3);
    border-right: 1px solid rgba(200, 200, 200, 0.3);
  }

  .tape-left {
    left: -8px;
    transform: rotate(-15deg);
  }

  .tape-right {
    right: -8px;
    transform: rotate(15deg);
  }

  /* ===== 卡片内容 ===== */
  .card-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .card-icon {
    font-size: 48px;
    display: block;
  }

  .card-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 32px;
    font-weight: 800;
    margin: 8px 0;
    color: #171717;
  }

  .card-description {
    font-size: 18px;
    color: #404040;
    line-height: 1.625;
    margin: 8px 0 16px;
  }

  .card-button {
    align-self: flex-start;
  }

  /* ===== 卡片装饰 ===== */
  .card-decoration {
    position: absolute;
    bottom: 16px;
    right: 16px;
    opacity: 0.1;
    pointer-events: none;
    transition: opacity 0.2s ease;

    .material-symbols-outlined {
      font-size: 60px;
    }
  }

  .mode-card:hover .card-decoration {
    opacity: 0.2;
  }

  .star-decoration {
    position: absolute;
    top: 16px;
    right: 16px;
    transform: rotate(12deg);

    .star-icon {
      font-size: 30px;
      color: #27e0a9;
      font-variation-settings: 'FILL' 1;
    }
  }

  /* ===== 响应式 ===== */
  @media (max-width: 768px) {
    .main {
      padding: 32px 16px;
      min-height: auto;
    }

    .hero {
      margin-bottom: 40px;
    }

    .hero-title {
      font-size: 36px;
    }

    .hero-subtitle {
      font-size: 20px;
    }

    .mode-grid {
      gap: 32px;
    }

    .mode-card {
      padding: 24px;
    }

    .brand-name {
      font-size: 20px;
    }
  }
`
