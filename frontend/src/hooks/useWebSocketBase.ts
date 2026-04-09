// frontend/src/hooks/useWebSocketBase.ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsEventUnion, WsMessageEvent, CheckpointStateData, TeachingMode } from '../types/observation'

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
}

/** WebSocket 基础 hook - 管理连接、消息分发、心跳和教学模式追踪 */
export function useWebSocketBase(sessionId: number): UseWebSocketBaseReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [messages, setMessages] = useState<WsMessageEvent[]>([])
  const [checkpointState, setCheckpointState] = useState<CheckpointStateData | null>(null)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [teachingMode, setTeachingMode] = useState<TeachingMode | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null)

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
    if (!sessionId) return

    const wsUrl = `ws://localhost:8000/ws/sessions/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnectionState('connected')
      startHeartbeat(ws)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEventUnion

        switch (data.type) {
          case 'message':
            setMessages((prev) => [...prev, data])
            break
          case 'checkpoint_state_change':
            setCheckpointState({
              index: data.index,
              checkpoint: data.checkpoint,
              progress: data.progress,
            })
            break
          case 'session_state':
            setTeachingMode(data.teaching_mode as TeachingMode)
            break
          case 'session_end':
            setSessionEnded(true)
            break
          case 'pong':
            // 心跳响应，无需处理
            break
          default:
            // connected / error 等事件暂不处理
            break
        }
      } catch {
        // JSON 解析失败，忽略
      }
    }

    ws.onclose = () => {
      setConnectionState('disconnected')
      stopHeartbeat()
    }

    ws.onerror = () => {
      setConnectionState('disconnected')
      stopHeartbeat()
    }

    return () => {
      stopHeartbeat()
      ws.close()
    }
  }, [sessionId, startHeartbeat, stopHeartbeat])

  return { connectionState, messages, checkpointState, sessionEnded, teachingMode }
}
