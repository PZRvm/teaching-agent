// frontend/src/views/ObservationView.tsx
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import Footer from '../components/Footer'
import { useWebSocketBase } from '../hooks/useWebSocketBase'
import { useElapsedTime } from '../hooks/useElapsedTime'
import { TEACHING_MODE_LABELS } from '../types/observation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ObservationView() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  // 如果没有 sessionId，导航回首页
  const sessionIdNum = sessionId ? Number(sessionId) : 0

  // 如果 sessionId 无效，不连接 WebSocket
  const shouldConnect = sessionIdNum > 0
  const { connectionState, messages, checkpointState, sessionEnded, teachingMode, sessionReady } =
    useWebSocketBase(shouldConnect ? sessionIdNum : -1)
  const elapsedTime = useElapsedTime(connectionState === 'connected')

  const teachingModeLabel = teachingMode ? TEACHING_MODE_LABELS[teachingMode] : null

  return (
    <Wrapper>
      <PageNav
        title="观察模式 - 实时观察"
        onBack={() => navigate('/')}
        right={
          <>
            {teachingModeLabel && <RoughBadge variant="blue" rotation={-1}>{teachingModeLabel}</RoughBadge>}
            {checkpointState && (
              <RoughBadge variant="yellow" rotation={2}>
                检查点 {checkpointState.progress.current}/{checkpointState.progress.total}
              </RoughBadge>
            )}
            <span className="elapsed-label">已进行</span>
            <span className="elapsed-time">{elapsedTime}</span>
            <span className="message-count">消息：{messages.length}</span>
          </>
        }
      />

      {/* 连接断开时显示提示 */}
      {connectionState === 'disconnected' && (
        <div className="loading-container">
          <div className="loading-card">
            <p className="loading-text">连接已断开</p>
            <p className="loading-subtext">请刷新页面重新连接</p>
          </div>
        </div>
      )}

      {/* 会话未就绪时显示加载状态 */}
      {!sessionReady && connectionState === 'connected' && (
        <div className="loading-container">
          <div className="loading-card">
            <p className="loading-text">正在准备课堂...</p>
            <p className="loading-subtext">AI 正在生成教学计划，请稍候</p>
          </div>
        </div>
      )}

      <div className="content-layout">
        <aside className="sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-title">检查点进度</h3>
            {checkpointState ? (
              <>
                <div className="current-checkpoint">
                  <p className="checkpoint-title-text">{checkpointState.checkpoint.title}</p>
                  <p className="checkpoint-progress-text">{checkpointState.progress.current}/{checkpointState.progress.total}</p>
                </div>
                <div className="checkpoint-list">
                  {Array.from({ length: checkpointState.progress.total }, (_, i) => (
                    <div
                      key={i}
                      className={`checkpoint-item ${i === checkpointState.index ? 'current' : ''} ${i < checkpointState.progress.current ? 'completed' : ''}`}
                    >
                      <span className="checkpoint-number">{i + 1}</span>
                      {i === checkpointState.index && (
                        <span className="checkpoint-label">进行中</span>
                      )}
                      {i < checkpointState.progress.current && (
                        <span className="checkpoint-label">已完成</span>
                      )}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="sidebar-empty">等待检查点数据...</p>
            )}
          </div>
        </aside>

        {/* 右侧：消息流 */}
        <main className="message-area">
          {sessionEnded && (
            <div className="session-ended-banner">会话已结束</div>
          )}

          {messages.length === 0 ? (
            <div className="empty-state">
              <p>暂无消息</p>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((msg, index) => (
                <div key={index} className="message-item">
                  <div className="message-header">
                    <span className="message-sender">{msg.sender}</span>
                    <span className="message-type-badge">{msg.message_type}</span>
                  </div>
                  <div className="message-bubble">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        p: ({ children }) => <p className="markdown-paragraph">{children}</p>,
                        ul: ({ children }) => <ul className="markdown-list">{children}</ul>,
                        ol: ({ children }) => <ol className="markdown-list">{children}</ol>,
                        li: ({ children }) => <li className="markdown-item">{children}</li>,
                        code({ inline, children, ...props }: Record<string, unknown>) {
                          const classNameAttr = inline
                            ? 'markdown-inline-code'
                            : 'markdown-code-block'
                          return <code className={classNameAttr} {...props}>{children}</code>
                        },
                        strong: ({ children }) => <strong>{children}</strong>,
                        em: ({ children }) => <em>{children}</em>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #fafafa;
  color: #1a1a1a;
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;
  display: flex;
  flex-direction: column;

  .elapsed-label {
    font-size: 14px;
    color: #6c757d;
  }

  .elapsed-time {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #1a1a1a;
    font-variant-numeric: tabular-nums;
  }

  .message-count {
    font-size: 14px;
    color: #6c757d;
    font-weight: 600;
  }

  /* ===== 加载状态 ===== */
  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    padding: 24px;
  }

  .loading-card {
    background: #ffffff;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    padding: 32px 48px;
    box-shadow: 3px 3px 0px 0px #1a1a1a;
    text-align: center;
  }

  .loading-text {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: #1a1a1a;
  }

  .loading-subtext {
    font-size: 14px;
    margin: 0;
    color: #6c757d;
  }

  /* ===== 内容布局 ===== */
  .content-layout {
    display: flex;
    flex: 1;
    gap: 24px;
    padding: 24px;
    max-width: 1280px;
    margin: 0 auto;
    width: 100%;
  }

  /* ===== 侧边栏 ===== */
  .sidebar {
    width: 280px;
    flex-shrink: 0;
  }

  .sidebar-card {
    background: #ffffff;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 3px 3px 0px 0px #1a1a1a;
  }

  .sidebar-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 16px;
    font-weight: 700;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #1a1a1a;
  }

  .sidebar-empty {
    color: #6c757d;
    font-size: 14px;
    text-align: center;
    padding: 20px 0;
  }

  .current-checkpoint {
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e5e5e5;
  }

  .checkpoint-title-text {
    font-weight: 600;
    font-size: 14px;
    margin: 0 0 4px 0;
    color: #1a1a1a;
  }

  .checkpoint-progress-text {
    font-size: 12px;
    margin: 0;
    color: #6c757d;
  }

  .checkpoint-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .checkpoint-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 14px;
    border: 1px solid transparent;

    &.current {
      border-color: #1a1a1a;
      font-weight: 700;
      box-shadow: 2px 2px 0px 0px #1a1a1a;
    }
  }

  .checkpoint-number {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #e5e5e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
  }

  .checkpoint-item.completed .checkpoint-number {
    background: #27e0a9;
  }

  .checkpoint-item.current .checkpoint-number {
    background: #2e5cff;
    color: #fff;
  }

  .checkpoint-label {
    font-size: 12px;
    margin-left: auto;
  }

  /* ===== 消息区域 ===== */
  .message-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .session-ended-banner {
    text-align: center;
    padding: 16px;
    background: #fce4ec;
    border: 2px solid #e63946;
    border-radius: 8px;
    font-weight: 700;
    color: #e63946;
    box-shadow: 3px 3px 0px 0px #1a1a1a;
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #6c757d;
  }

  .message-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .message-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .message-sender {
    font-weight: 700;
    font-size: 14px;
  }

  .message-type-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    background: #f0f0f0;
    color: #1a1c1c;
    border: 1px solid #1a1a1a;
    box-shadow: 1px 1px 0px 0px #1a1a1a;
  }

  .message-bubble {
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
    background: #ffffff;
    line-height: 1.6;

    // Markdown 样式
    .markdown-paragraph {
      margin: 0 0 12px 0;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .markdown-list {
      margin: 0 0 12px 20px;
      padding-left: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .markdown-item {
      margin-bottom: 4px;
    }

    .markdown-inline-code {
      background: #f4f4f4;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;
      color: #e83e8c;
    }

    .markdown-code-block {
      display: block;
      background: #2d2d2d;
      color: #f8f8f2;
      padding: 12px;
      border-radius: 6px;
      margin: 12px 0;
      overflow-x: auto;
      font-family: 'Courier New', monospace;
      font-size: 0.9em;

      &:last-child {
        margin-bottom: 0;
      }
    }

    // Markdown 标题样式
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      margin-top: 16px;
      margin-bottom: 12px;
      font-weight: 700;
      line-height: 1.3;

      &:first-child {
        margin-top: 0;
      }
    }

    h1 {
      font-size: 1.5em;
    }

    h2 {
      font-size: 1.3em;
    }

    h3 {
      font-size: 1.1em;
    }

    // Markdown 其他元素
    blockquote {
      border-left: 4px solid #1a1a1a;
      padding-left: 16px;
      margin: 12px 0;
      color: #6c757d;
      font-style: italic;
    }

    hr {
      border: none;
      border-top: 1px solid #e5e5e5;
      margin: 16px 0;
    }

    a {
      color: #2e5cff;
      text-decoration: underline;

      &:hover {
        color: #1a4adb;
      }
    }

    table {
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0;

      th,
      td {
        border: 1px solid #e5e5e5;
        padding: 8px;
        text-align: left;
      }

      th {
        background: #f8f9fa;
        font-weight: 700;
      }
    }
  }

  /* ===== 响应式 ===== */
  @media (max-width: 768px) {
    .content-layout {
      flex-direction: column;
    }

    .sidebar {
      width: 100%;
    }
  }
`
