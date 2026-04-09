// frontend/src/views/ObservationView.tsx
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import { useWebSocket } from '../hooks/useWebSocket'
import { useElapsedTime } from '../hooks/useElapsedTime'
import { TEACHING_MODE_LABELS } from '../types/observation'

export default function ObservationView() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const sessionIdNum = sessionId ? Number(sessionId) : 0
  const { connectionState, messages, checkpointState, sessionEnded, teachingMode } =
    useWebSocket(sessionIdNum)
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

      <div className="content-layout">
        {/* 左侧：检查点进度 */}
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
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
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
