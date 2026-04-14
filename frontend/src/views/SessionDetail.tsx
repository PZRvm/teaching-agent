import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import Footer from '../components/Footer'
import { getSessionMessages, getSessionList } from '../apis/session'
import { getCheckpointPlan } from '../apis/observation'
import type { SessionSummary, SessionMessage } from '../apis/session'
import type { CheckpointItem } from '../apis/observation'

const TEACHING_MODE_LABELS: Record<string, string> = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
}

const MODE_BADGE_VARIANT: Record<string, 'yellow' | 'blue' | 'green'> = {
  didactic: 'yellow',
  heuristic: 'blue',
  discussion: 'green',
}

const STATUS_LABELS: Record<string, string> = {
  running: '进行中',
  completed: '已完成',
  interrupted: '已中断',
}

const MESSAGE_TYPE_LABELS: Record<string, string> = {
  LECTURE: '讲授',
  CHECKPOINT_QUESTION: '提问',
  ANSWER_TO_CHECKPOINT: '回答',
  ASK_QUESTION: '主动提问',
  REPLY_TO_STUDENT: '回复',
  ASSIGN_HOMEWORK: '布置作业',
  HOMEWORK_SUBMISSION: '提交作业',
  HOMEWORK_FEEDBACK: '作业反馈',
  END_FEEDBACK: '结束反馈',
}

const MESSAGE_TAG_BG: Record<string, string> = {
  LECTURE: '#E3F2FD',
  CHECKPOINT_QUESTION: '#FFF9C4',
  ANSWER_TO_CHECKPOINT: '#E8F5E9',
  ASK_QUESTION: '#FCE4EC',
  REPLY_TO_STUDENT: '#E3F2FD',
  ASSIGN_HOMEWORK: '#fafafa',
  HOMEWORK_SUBMISSION: '#fafafa',
  HOMEWORK_FEEDBACK: '#E3F2FD',
  END_FEEDBACK: '#FFF9C4',
}

const TEACHER_SENDERS = ['教师', 'teacher', 'Teacher']

function isTeacher(sender: string): boolean {
  return TEACHER_SENDERS.some((t) => sender.includes(t))
}

function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return ''
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}分钟`
  const hours = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hours}小时${remainMins}分钟`
}

function formatDate(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [messages, setMessages] = useState<SessionMessage[]>([])
  const [checkpoints, setCheckpoints] = useState<CheckpointItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    if (!sessionId) return
    const sid = Number(sessionId)
    setLoading(true)
    setError(null)

    try {
      const [list, msgs, plan] = await Promise.all([
        getSessionList().then((l) => l.find((s) => s.id === sid) ?? null),
        getSessionMessages(sid),
        getCheckpointPlan(sid).catch(() => null),
      ])
      setSession(list)
      setMessages(msgs)
      if (plan) setCheckpoints(plan.checkpoints)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    void fetchData()
  }, [fetchData])

  if (loading) return <Wrapper><div className="loading-text">加载中...</div></Wrapper>
  if (error || !session) return <Wrapper><div className="error-text">{error ?? '会话不存在'}</div></Wrapper>

  return (
    <Wrapper>
      <PageNav
        title="课堂详情"
        onBack={() => navigate('/history')}
        backLabel="← 返回历史"
        right={
          <RoughBadge variant={MODE_BADGE_VARIANT[session.teaching_mode] ?? 'blue'}>
            {TEACHING_MODE_LABELS[session.teaching_mode] ?? session.teaching_mode}
          </RoughBadge>
        }
      />

      <main className="main">
        <div className="session-header">
          <h1 className="session-topic">{session.topic}</h1>
          <div className="session-meta">
            <RoughBadge variant={session.status === 'completed' ? 'green' : 'yellow'}>
              {STATUS_LABELS[session.status] ?? session.status}
            </RoughBadge>
            <span className="meta-item">{formatDate(session.start_time)}</span>
            {session.duration_seconds !== null && (
              <span className="meta-item">{formatDuration(session.duration_seconds)}</span>
            )}
            <span className="meta-item">{session.student_count} 名学生</span>
          </div>
        </div>

        <div className="content-layout">
          <div className="timeline-panel">
            {messages.length === 0 && (
              <div className="empty-messages">暂无消息记录</div>
            )}
            {messages.map((msg) => {
              const teacher = isTeacher(msg.sender)
              return (
                <div key={msg.id} className={`message-item ${teacher ? 'teacher' : 'student'}`}>
                  <div className="message-dot" aria-hidden="true" />
                  <div className="message-card">
                    <div className="message-header">
                      <span className="sender-name">{msg.sender}</span>
                      <span
                        className="message-type-tag"
                        style={{ background: MESSAGE_TAG_BG[msg.message_type] ?? '#fafafa' }}
                      >
                        {MESSAGE_TYPE_LABELS[msg.message_type] ?? msg.message_type}
                      </span>
                      <span className="message-time">{formatTime(msg.timestamp)}</span>
                    </div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                </div>
              )
            })}
          </div>

          {checkpoints.length > 0 && (
            <div className="checkpoint-panel">
              <div className="tape" aria-hidden="true" />
              <h2 className="panel-title">检查点进度</h2>
              <div className="checkpoint-list">
                {checkpoints.map((cp, index) => (
                  <div key={index} className={`checkpoint-item state-${cp.state}`}>
                    <span className="checkpoint-icon" aria-hidden="true">
                      {cp.state === 'complete' ? '\u2713' : cp.state === 'teaching' || cp.state === 'questions' ? '\u25CF' : '\u25CB'}
                    </span>
                    <span className="checkpoint-title">{cp.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
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

  .loading-text,
  .error-text {
    text-align: center;
    font-size: 18px;
    padding: 64px 0;
    color: #525252;
  }

  .error-text {
    color: #b7102a;
  }

  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 24px 24px 64px;
  }

  .session-header {
    margin-bottom: 32px;
  }

  .session-topic {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 12px;
    color: #171717;
  }

  .session-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .meta-item {
    font-size: 14px;
    color: #525252;
  }

  .content-layout {
    display: flex;
    flex-direction: column;
    gap: 24px;

    @media (min-width: 768px) {
      flex-direction: row;
    }
  }

  .timeline-panel {
    flex: 1;
    min-width: 0;
  }

  .empty-messages {
    text-align: center;
    color: #737373;
    padding: 48px 0;
    font-size: 16px;
  }

  .message-item {
    position: relative;
    padding-left: 32px;
    padding-bottom: 20px;
    border-left: 2px dashed #d4d4d4;

    &:last-child {
      padding-bottom: 0;
      border-left-color: transparent;
    }
  }

  .message-dot {
    position: absolute;
    left: 8px;
    top: 12px;
    width: 10px;
    height: 10px;
    border: 2px solid #1a1a1a;
    background: #fafafa;
  }

  .message-item.teacher .message-dot {
    background: #2e5cff;
  }

  .message-item.student .message-dot {
    background: #27e0a9;
    transform: rotate(45deg);
  }

  .message-card {
    background: #fafafa;
    border: 2px solid #1a1a1a;
    padding: 16px;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
  }

  .message-item.teacher .message-card {
    border-left: 4px solid #2e5cff;
  }

  .message-item.student .message-card {
    border-left: 4px solid #27e0a9;
    transform: rotate(-0.3deg);
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }

  .sender-name {
    font-weight: 700;
    font-size: 14px;
    color: #171717;
  }

  .message-type-tag {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border: 1px solid #1a1a1a;
    color: #525252;
  }

  .message-time {
    font-size: 12px;
    color: #a3a3a3;
    margin-left: auto;
  }

  .message-content {
    font-size: 15px;
    line-height: 1.6;
    color: #404040;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .checkpoint-panel {
    width: 100%;
    background: #fff9c4;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 24px;
    position: relative;
    transform: rotate(0.5deg);

    @media (min-width: 768px) {
      width: 280px;
      min-width: 280px;
    }
  }

  .tape {
    position: absolute;
    top: -16px;
    right: -8px;
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    transform: rotate(15deg);
    border-left: 1px solid rgba(200, 200, 200, 0.3);
    border-right: 1px solid rgba(200, 200, 200, 0.3);
  }

  .panel-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 18px;
    font-weight: 800;
    margin: 0 0 16px;
    color: #171717;
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
    font-size: 14px;
    padding: 4px 0;

    &.state-complete {
      color: #006247;
    }

    &.state-teaching,
    &.state-questions {
      color: #2e5cff;
      font-weight: 700;
    }

    &.state-pending {
      color: #525252;
    }
  }

  .checkpoint-icon {
    font-size: 14px;
    width: 20px;
    text-align: center;
    flex-shrink: 0;
  }

  .checkpoint-title {
    line-height: 1.4;
  }

  @media (max-width: 768px) {
    .session-topic {
      font-size: 24px;
    }

    .checkpoint-panel {
      transform: none;
    }
  }
`
