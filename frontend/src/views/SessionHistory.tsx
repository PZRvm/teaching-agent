import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import RoughButton from '../components/RoughButton'
import Footer from '../components/Footer'
import { getSessionList } from '../apis/session'
import type { SessionSummary } from '../apis/session'
import { formatDuration, formatDate } from '../utils/format'
import { TEACHING_MODE_LABELS, MODE_BADGE_VARIANT, STATUS_LABELS } from '../types/observation'

export default function SessionHistory() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSessions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSessionList()
      setSessions(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchSessions()
  }, [fetchSessions])

  return (
    <Wrapper>
      <div className="bg-decoration-left" aria-hidden="true" />
      <div className="bg-decoration-right" aria-hidden="true" />

      <PageNav title="课堂历史记录" onBack={() => navigate('/')} backLabel="← 首页" />

      <main className="main">
        {loading && <div className="loading-text">加载中...</div>}
        {error && <div className="error-text">{error}</div>}

        {!loading && sessions.length === 0 && (
          <div className="empty-state">
            <div className="empty-card">
              <span className="material-symbols-outlined empty-icon">history</span>
              <p className="empty-title">还没有课堂记录</p>
              <p className="empty-desc">开始一节观察模式课程，记录将显示在这里</p>
              <RoughButton
                variant="primary"
                onClick={() => navigate('/observation/config')}
              >
                开始观察 →
              </RoughButton>
            </div>
          </div>
        )}

        {!loading && sessions.length > 0 && (
          <div className="session-grid">
            {sessions.map((session, index) => (
              <article
                key={session.id}
                className={`session-card mode-${session.teaching_mode} ${index % 2 === 0 ? 'rotate-left' : 'rotate-right'}`}
                onClick={() => navigate(`/history/${session.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') navigate(`/history/${session.id}`)
                }}
              >
                <div className="tape tape-left" aria-hidden="true" />
                <div className="card-content">
                  <div className="card-tags">
                    <RoughBadge variant={MODE_BADGE_VARIANT[session.teaching_mode] ?? 'blue'}>
                      {TEACHING_MODE_LABELS[session.teaching_mode] ?? session.teaching_mode}
                    </RoughBadge>
                    <RoughBadge
                      variant={session.status === 'completed' ? 'green' : session.status === 'running' ? 'blue' : 'yellow'}
                    >
                      {STATUS_LABELS[session.status] ?? session.status}
                    </RoughBadge>
                  </div>
                  <h2 className="card-title">{session.topic}</h2>
                  <div className="card-meta">
                    <span>{formatDate(session.start_time)}</span>
                    {session.duration_seconds !== null && (
                      <>
                        <span className="meta-divider">·</span>
                        <span>{formatDuration(session.duration_seconds)}</span>
                      </>
                    )}
                    <span className="meta-divider">·</span>
                    <span>{session.student_count} 名学生</span>
                  </div>
                  {session.checkpoint_progress && (
                    <div className="progress-section">
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{
                            width: `${session.checkpoint_progress.total > 0
                              ? (session.checkpoint_progress.completed / session.checkpoint_progress.total) * 100
                              : 0}%`,
                          }}
                        />
                      </div>
                      <span className="progress-text">
                        {session.checkpoint_progress.completed}/{session.checkpoint_progress.total} 检查点
                      </span>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
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
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;

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

  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 32px 24px 64px;
    position: relative;
    z-index: 1;
  }

  .loading-text,
  .error-text {
    text-align: center;
    font-size: 18px;
    color: #525252;
    padding: 64px 0;
  }

  .error-text {
    color: #b7102a;
  }

  .empty-state {
    display: flex;
    justify-content: center;
    padding: 64px 0;
  }

  .empty-card {
    text-align: center;
    padding: 48px 40px;
    border: 3px dashed #d4d4d4;
    max-width: 400px;
  }

  .empty-icon {
    font-size: 64px;
    color: #d4d4d4;
    display: block;
    margin-bottom: 16px;
  }

  .empty-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    font-weight: 700;
    margin: 0 0 8px;
    color: #525252;
  }

  .empty-desc {
    font-size: 16px;
    color: #737373;
    margin: 0 0 24px;
    line-height: 1.6;
  }

  .session-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 32px;

    @media (min-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .session-card {
    position: relative;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 28px;
    cursor: pointer;
    transition: transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
      box-shadow: 8px 8px 0px 0px #1a1a1a;
      transform: translate(-4px, -4px);
    }

    &:focus-visible {
      outline: 2px dashed #1a1a1a;
      outline-offset: 4px;
    }

    &.mode-didactic {
      background: #fff9c4;
    }

    &.mode-heuristic {
      background: #e3f2fd;
    }

    &.mode-discussion {
      background: #e8f5e9;
    }

    &.rotate-left {
      transform: rotate(-0.5deg);

      &:hover {
        transform: translate(-4px, -4px) rotate(-0.5deg);
      }
    }

    &.rotate-right {
      transform: rotate(0.5deg);

      &:hover {
        transform: translate(-4px, -4px) rotate(0.5deg);
      }
    }
  }

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

  .card-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .card-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    font-weight: 800;
    margin: 4px 0;
    color: #171717;
    line-height: 1.3;
  }

  .card-meta {
    font-size: 14px;
    color: #525252;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .meta-divider {
    color: #d4d4d4;
  }

  .progress-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
  }

  .progress-bar {
    flex: 1;
    height: 12px;
    border: 2px solid #1a1a1a;
    background: #fafafa;
    clip-path: polygon(0% 2%, 100% 0%, 98% 100%, 2% 98%);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: #27e0a9;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 13px;
    font-weight: 700;
    color: #525252;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .main {
      padding: 16px 16px 48px;
    }

    .card-title {
      font-size: 20px;
    }
  }
`
