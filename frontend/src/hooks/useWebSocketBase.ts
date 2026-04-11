// frontend/src/hooks/useWebSocketBase.ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsEventUnion, WsMessageEvent, CheckpointStateData, CheckpointState, TeachingMode } from '../types/observation'

/** WebSocket 连接状态 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

/** useWebSocketBase hook 返回值 */
export interface UseWebSocketBaseReturn {
  /** 当前连接状态 */
  connectionState: ConnectionState
  /** 收到的所有消息 */
  messages: WsMessageEvent[]
  /** 当前检查点状态 */
  checkpointState: CheckpointStateData | null
  /** 会话是否已结束 */
  sessionEnded: boolean
  /** 教学模式（从 session_state 事件获取，初始为 null） */
  teachingMode: TeachingMode | null
  /** 会话是否已就绪（orchestrator 已创建并开始运行） */
  sessionReady: boolean
}

/** WebSocket 基础 hook - 管理连接、消息分发、心跳和教学模式追踪 */
export function useWebSocketBase(sessionId: number): UseWebSocketBaseReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [messages, setMessages] = useState<WsMessageEvent[]>([])
  const [checkpointState, setCheckpointState] = useState<CheckpointStateData | null>(null)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [teachingMode, setTeachingMode] = useState<TeachingMode | null>(null)
  const [sessionReady, setSessionReady] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const sessionIdRef = useRef<number>(sessionId) // 追踪当前连接的 sessionId

  const startHeartbeat = useCallback((ws: WebSocket) => {
    // 清除旧的心跳
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
    }
    heartbeatRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30_000)
  }, [])

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
      heartbeatRef.current = null
    }
  }, [])

  useEffect(() => {
    // 明确检查无效的 sessionId（0 或负数）
    if (!sessionId || sessionId <= 0) {
      // 清理无效 sessionId 的连接
      if (wsRef.current) {
        wsRef.current.close(1000, 'Invalid sessionId')
        wsRef.current = null
      }
      return
    }

    // 如果 sessionId 没有变化，不重新连接
    if (sessionIdRef.current === sessionId && wsRef.current) {
      return
    }

    // 关闭旧连接（如果存在且 sessionId 不同）
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close(1000, 'Session changed')
    }

    sessionIdRef.current = sessionId

    // 开发环境通过 Vite 代理连接 WebSocket，生产环境直连后端
    const wsBase = import.meta.env.DEV
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
      : (import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000')
    const wsUrl = `${wsBase}/ws/sessions/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket 连接成功 (session_id=%d)', sessionId)
      setConnectionState('connected')
      startHeartbeat(ws)
    }

    ws.onerror = (error) => {
      // 检查是否是连接被拒绝（可能是 session 不存在）
      if (ws.readyState === WebSocket.CLOSED) {
        console.error('WebSocket 连接被拒绝，可能的原因：')
        console.error('1. Session ID 不存在（后端重启后旧的 Session ID 失效）')
        console.error('2. 后端未运行')
        console.error('3. 浏览器代理拦截了 WebSocket 连接')
        console.error('')
        console.error('解决方法：')
        console.error('- 刷新页面，重新开始观察模式')
        console.error('- 如果使用代理，请将 localhost 添加到代理绕过列表')
        console.error('- Chrome: 设置 → 系统 → 打开代理设置 → 绕过代理设置')
        console.error('- Firefox: 设置 → 网络设置 → 代理 → 无代理 for: localhost, 127.0.0.1')
      }
      console.error('WebSocket 错误详情:', {
        sessionId,
        readyState: ws.readyState,
        url: ws.url,
        error,
      })
      // 不要立即设置为 disconnected，因为可能还有机会恢复
      // setConnectionState('disconnected')
      // stopHeartbeat()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEventUnion
        console.log('WebSocket 收到消息:', data.type, data)

        switch (data.type) {
          case 'message':
            setMessages((prev) => [...prev, data])
            break
          case 'checkpoint_state_change':
            setCheckpointState({
              index: data.index,
              checkpoint: {
                ...data.checkpoint,
                state: data.checkpoint.state as CheckpointState,
              },
              progress: data.progress,
            })
            break
          case 'session_state':
            setTeachingMode(data.teaching_mode as TeachingMode)
            if (data.status === 'ended') {
              setSessionEnded(true)
            }
            if (data.status === 'running') {
              setSessionReady(true)
            }
            break
          case 'session_end':
            setSessionEnded(true)
            break
          case 'connected':
            // connected 事件包含 ready 字段，表示 orchestrator 是否已就绪
            if ('ready' in data && typeof data.ready === 'boolean') {
              setSessionReady(data.ready)
            }
            break
          case 'pong':
            // 心跳响应，无需处理
            break
          case 'error':
            // 错误事件，记录但不改变连接状态
            console.error('WebSocket 错误事件:', data)
            break
          default:
            // 其他未知事件暂不处理
            break
        }
      } catch {
        // JSON 解析失败，忽略
      }
    }

    ws.onclose = (event) => {
      console.warn('WebSocket 关闭详情:', {
        sessionId,
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      })
      setConnectionState('disconnected')
      stopHeartbeat()
      // 只有当这是当前 sessionId 的连接时才清理
      if (sessionIdRef.current === sessionId) {
        wsRef.current = null
      }
      // 正常关闭：code 1000 或无 code
      if (event.code === 1000 || event.code === 1005) {
        console.log('WebSocket 连接正常关闭')
      } else {
        console.error('WebSocket 连接异常关闭:', event.code, event.reason)
      }
    }

    return () => {
      // 只在组件卸载或 sessionId 变化时关闭连接
      // 避免在 React 严格模式下重复清理
      if (wsRef.current === ws) {
        stopHeartbeat()
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close(1000, 'Component unmounting')
        }
        wsRef.current = null
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  return { connectionState, messages, checkpointState, sessionEnded, teachingMode, sessionReady }
}
