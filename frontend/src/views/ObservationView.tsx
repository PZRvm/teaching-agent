// frontend/src/views/ObservationView.tsx
import { useParams, useNavigate } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import Footer from '../components/Footer'
import { useWebSocketBase } from '../hooks/useWebSocketBase'
import { useElapsedTime } from '../hooks/useElapsedTime'
import { useSessionMessages } from '../hooks/useSessionMessages'
import { useCheckpointPlan } from '../hooks/useCheckpointPlan'
import { useCheckpointProgress } from '../hooks/useCheckpointProgress'
import { getSessionDetail } from '../apis/session'
import { TEACHING_MODE_LABELS } from '../types/observation'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function ObservationView() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const sessionIdNum = sessionId ? Number(sessionId) : 0

  // 先获取会话状态，判断是否已完成
  const [sessionStatus, setSessionStatus] = useState<string | null>(null)
  const [statusLoading, setStatusLoading] = useState(sessionIdNum > 0)

  useEffect(() => {
    if (sessionIdNum <= 0) return
    getSessionDetail(sessionIdNum)
      .then((detail) => setSessionStatus(detail.status))
      .catch(() => setSessionStatus(null))
      .finally(() => setStatusLoading(false))
  }, [sessionIdNum])

  const isCompleted = sessionStatus === 'completed'

  // 已完成的会话不连接 WebSocket，使用 HTTP-only 模式
  const wsSessionId = isCompleted ? -1 : (sessionIdNum > 0 ? sessionIdNum : -1)
  const { connectionState, messages: wsMessages, checkpointState, sessionEnded, teachingMode, sessionReady } =
    useWebSocketBase(wsSessionId)
  const { messages, loading: historyLoading } = useSessionMessages(
    sessionIdNum > 0 ? sessionIdNum : -1,
    wsMessages,
  )
  const elapsedTime = useElapsedTime(connectionState === 'connected' && !isCompleted)
  const { plan: checkpointPlan } = useCheckpointPlan(
    sessionIdNum > 0 ? sessionIdNum : -1,
    sessionReady || isCompleted,
  )
  const { progress: httpProgress, loading: progressLoading } = useCheckpointProgress(
    sessionIdNum > 0 ? sessionIdNum : -1,
  )

  // WebSocket 实时状态优先，HTTP 请求作为初始值
  const effectiveCheckpointState = checkpointState ?? httpProgress
  const initialLoading = (statusLoading || historyLoading || progressLoading) && messages.length === 0 && !effectiveCheckpointState

  // 教学模式：WebSocket 实时值优先，否则从 session detail 获取
  const teachingModeLabel = teachingMode
    ? TEACHING_MODE_LABELS[teachingMode]
    : null

  // 自动滚动到最新消息
  const messageAreaRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (messageAreaRef.current) {
      messageAreaRef.current.scrollTop = messageAreaRef.current.scrollHeight
    }
  }, [messages.length])

  return (
    <Wrapper>
      <PageNav
        title={isCompleted ? '观察模式 - 课程回顾' : '观察模式 - 实时观察'}
        onBack={() => navigate('/')}
        right={
          <>
            {isCompleted && <RoughBadge variant="green" rotation={-1}>课程已结束</RoughBadge>}
            {teachingModeLabel && !isCompleted && <RoughBadge variant="blue" rotation={-1}>{teachingModeLabel}</RoughBadge>}
            {effectiveCheckpointState && (
              <RoughBadge variant="yellow" rotation={2}>
                检查点 {effectiveCheckpointState.progress.current}/{effectiveCheckpointState.progress.total}
              </RoughBadge>
            )}
            {!isCompleted && <span className="elapsed-label">已进行</span>}
            {!isCompleted && <span className="elapsed-time">{elapsedTime}</span>}
            <span className="message-count">消息：{messages.length}</span>
          </>
        }
      />

      {/* 页面初始加载 */}
      {initialLoading && (
        <div className="loading-container">
          <div className="loading-card">
            <p className="loading-text">{isCompleted ? '正在加载课程记录...' : '正在加载课堂数据...'}</p>
          </div>
        </div>
      )}

      {/* 加载历史消息时显示提示（仅实时观察模式） */}
      {historyLoading && !isCompleted && connectionState === 'connected' && sessionReady && (
        <div className="loading-container">
          <div className="loading-card">
            <p className="loading-text">正在加载历史消息...</p>
          </div>
        </div>
      )}

      {/* 会话未就绪时显示加载状态（仅实时观察模式） */}
      {!sessionReady && !isCompleted && connectionState === 'connected' && (
        <div className="loading-container">
          <div className="loading-card">
            <p className="loading-text">正在准备课堂...</p>
            <p className="loading-subtext">AI 正在生成教学计划，请稍候</p>
          </div>
        </div>
      )}

      {/* 内容区域：实时观察需要 sessionReady 或有消息，课程回顾只需有数据 */}
      {(isCompleted || (sessionReady && connectionState === 'connected') || messages.length > 0) && (
      <div className="content-layout">
        <aside className="sidebar">
          <div className="sidebar-card">
            <h3 className="sidebar-title">检查点进度</h3>
            {effectiveCheckpointState ? (
              <>
                <div className="current-checkpoint">
                  <p className="checkpoint-title-text">{effectiveCheckpointState.checkpoint.title}</p>
                  <p className="checkpoint-progress-text">{effectiveCheckpointState.progress.current}/{effectiveCheckpointState.progress.total}</p>
                </div>
                <div className="checkpoint-list">
                  {(checkpointPlan ?? effectiveCheckpointState).checkpoints
                    ? (checkpointPlan ?? effectiveCheckpointState).checkpoints!.map((cp, i) => {
                        const isCurrent = i === effectiveCheckpointState.index
                        const state = cp.state as string
                        return (
                          <div
                            key={i}
                            className={`checkpoint-item state-${state} ${isCurrent ? 'current' : ''}`}
                          >
                            <span className="checkpoint-number">{i + 1}</span>
                            <span className="checkpoint-name">{cp.title}</span>
                            <span className="checkpoint-label">
                              {state === 'teaching' && '讲授中'}
                              {state === 'questions' && '提问中'}
                              {state === 'complete' && '已完成'}
                              {state === 'pending' && !isCurrent && '待开始'}
                            </span>
                          </div>
                        )
                      })
                    : Array.from({ length: effectiveCheckpointState.progress.total }, (_, i) => (
                        <div
                          key={i}
                          className={`checkpoint-item ${i === effectiveCheckpointState.index ? 'current' : ''} ${i < effectiveCheckpointState.index ? 'completed' : ''}`}
                        >
                          <span className="checkpoint-number">{i + 1}</span>
                          {i === effectiveCheckpointState.index && (
                            <span className="checkpoint-label">进行中</span>
                          )}
                          {i < effectiveCheckpointState.index && (
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
        <div className="message-column">
          {connectionState === 'disconnected' && !isCompleted && !sessionEnded && (
            <div className="session-ended-banner">连接已断开，请刷新页面重新连接</div>
          )}

          <main className="message-area" ref={messageAreaRef}>
            {sessionEnded && !isCompleted && (
              <div className="session-ended-banner">会话已结束</div>
            )}

            {messages.length === 0 ? (
              <div className="empty-state">
                <p>暂无消息</p>
              </div>
            ) : (
              <div className="message-list">
                {messages.map((msg, index) => (
                  <div key={`${msg.sender}-${msg.message_type}-${index}`} className="message-item">
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
                          code({ className, children, ...props }: Record<string, unknown>) {
                            const isBlock = typeof className === 'string' && className.includes('language-')
                            const classNameAttr = isBlock
                              ? 'markdown-code-block'
                              : 'markdown-inline-code'
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
      </div>
      )}

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  height: 100dvh;
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
    min-height: 0;
    overflow: hidden;
  }

  /* ===== 侧边栏 ===== */
  .sidebar {
    width: 280px;
    flex-shrink: 0;
    overflow-y: auto;
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
    flex-shrink: 0;
  }

  .checkpoint-name {
    flex: 1;
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .checkpoint-item.state-complete .checkpoint-number {
    background: #27e0a9;
  }

  .checkpoint-item.state-teaching,
  .checkpoint-item.state-questions {
    font-weight: 700;
  }

  .checkpoint-item.state-teaching .checkpoint-number {
    background: #2e5cff;
    color: #fff;
  }

  .checkpoint-item.state-questions .checkpoint-number {
    background: #fff9c4;
  }

  .checkpoint-item.state-pending .checkpoint-number {
    background: #e5e5e5;
  }

  .checkpoint-item.current .checkpoint-number {
    background: #2e5cff;
    color: #fff;
  }

  .checkpoint-label {
    font-size: 12px;
    margin-left: auto;
    white-space: nowrap;
  }

  /* ===== 消息列（包含 banner + 消息区） ===== */
  .message-column {
    flex: 1;
    width: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
  }

  /* ===== 消息区域 ===== */
  .message-area {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    padding: 24px 16px;
    background: #ffffff;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
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
    gap: 16px;
    padding: 0 16px;
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
