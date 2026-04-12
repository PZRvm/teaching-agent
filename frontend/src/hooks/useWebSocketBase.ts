// frontend/src/hooks/useWebSocketBase.ts
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsEventUnion, WsMessageEvent, CheckpointStateData, CheckpointState, TeachingMode } from '../types/observation'

/** WebSocket 连接状态 */
export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

/** useWebSocketBase hook 返回值 */
export interface UseWebSocketBaseReturn {
  /** 当前连接状态 */
  connectionState: ConnectionState
  /** 收到的所有实时消息（不包含历史消息） */
  messages: WsMessageEvent[]
  /** 当前检查点状态（从 checkpoint_state_change 事件获取） */
  checkpointState: CheckpointStateData | null
  /** 会话是否已结束 */
  sessionEnded: boolean
  /** 教学模式（从 session_state 事件获取，初始为 null） */
  teachingMode: TeachingMode | null
  /** 会话是否已就绪（orchestrator 已创建并开始运行） */
  sessionReady: boolean
}

/**
 * WebSocket 基础 hook - 管理连接、消息分发、心跳和教学模式追踪.
 *
 * 职责：
 * - 根据 sessionId 建立 WebSocket 连接
 * - 30 秒间隔发送 ping 心跳包保持连接
 * - 分发不同类型的 WebSocket 事件到对应的状态更新
 * - 追踪会话状态（教学模式、检查点进度、就绪/结束）
 *
 * 事件分发：
 * - message: 追加到 messages 数组
 * - checkpoint_state_change: 更新 checkpointState
 * - session_state: 更新 teachingMode，检测 running/ended 状态
 * - connected: 根据 ready 字段更新 sessionReady
 * - session_end: 标记 sessionEnded
 * - pong: 心跳响应，忽略
 * - error: 记录错误日志
 *
 * @param sessionId 会话 ID，无效时不建立连接
 * @returns 连接状态、消息列表和各种会话状态
 */
export function useWebSocketBase(sessionId: number): UseWebSocketBaseReturn {
  const [connectionState, setConnectionState] = useState<ConnectionState>('connecting')
  const [messages, setMessages] = useState<WsMessageEvent[]>([])
  const [checkpointState, setCheckpointState] = useState<CheckpointStateData | null>(null)
  const [sessionEnded, setSessionEnded] = useState(false)
  const [teachingMode, setTeachingMode] = useState<TeachingMode | null>(null)
  const [sessionReady, setSessionReady] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const sessionIdRef = useRef<number>(sessionId)

  /** 启动心跳定时器，每 30 秒发送一次 ping */
  const startHeartbeat = useCallback((ws: WebSocket) => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
    }
    heartbeatRef.current = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30_000)
  }, [])

  /** 停止心跳定时器 */
  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current)
      heartbeatRef.current = null
    }
  }, [])

  useEffect(() => {
    // 无效 sessionId 不建立连接
    if (!sessionId || sessionId <= 0) {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Invalid sessionId')
        wsRef.current = null
      }
      return
    }

    // sessionId 未变化且连接存在时，跳过重复连接
    if (sessionIdRef.current === sessionId && wsRef.current) {
      return
    }

    // sessionId 变化时，关闭旧连接
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close(1000, 'Session changed')
    }

    sessionIdRef.current = sessionId

    // 根据 Vite 代理或生产环境 URL 构建 WebSocket 地址
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
        console.error('- Firefox: 设置 → 网络设置 → 代理 → 无代理 for: localhost, 127.0.1.1')
      }
      console.error('WebSocket 错误详情:', {
        sessionId,
        readyState: ws.readyState,
        url: ws.url,
        error,
      })
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsEventUnion
        console.log('WebSocket 收到消息:', data.type, data)

        switch (data.type) {
          case 'message':
            // 教学消息（讲座、提问、回答等），追加到消息列表
            setMessages((prev) => [...prev, data])
            break
          case 'checkpoint_state_change':
            // 检查点状态变更，更新当前检查点信息和进度
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
            // 会话状态变更，更新教学模式和结束/就绪状态
            setTeachingMode(data.teaching_mode as TeachingMode)
            if (data.status === 'ended') {
              setSessionEnded(true)
            }
            if (data.status === 'running') {
              setSessionReady(true)
            }
            break
          case 'session_end':
            // 会话结束事件
            setSessionEnded(true)
            break
          case 'connected':
            // 连接确认事件，包含 ready 字段表示 orchestrator 是否就绪
            if ('ready' in data && typeof data.ready === 'boolean') {
              setSessionReady(data.ready)
            }
            break
          case 'pong':
            // 心跳响应，无需处理
            break
          case 'error':
            // 错误事件，记录日志但不改变连接状态
            console.error('WebSocket 错误事件:', data)
            break
          default:
            // 其他未知事件暂不处理
            break
        }
      } catch {
        // JSON 解析失败，忽略该消息
      }
    }

    ws.onclose = (event) => {
      console.warn('WebSocket 关闭详情:', {
        sessionId,
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean,
      })
      console.log('WebSocket 连接已关闭 (session_id=%d)', sessionId)
      setConnectionState('disconnected')
      stopHeartbeat()
      // 只有当前 sessionId 的连接关闭时才清理 ref
      if (sessionIdRef.current === sessionId) {
        wsRef.current = null
      }
      if (event.code === 1000 || event.code === 1005) {
        console.log('WebSocket 连接正常关闭')
      } else {
        console.error('WebSocket 连接异常关闭:', event.code, event.reason)
      }
    }

    return () => {
      // 组件卸载或 sessionId 变化时关闭连接并停止心跳
      if (wsRef.current === ws) {
        stopHeartbeat()
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close(1000, 'Component unmounting')
        }
        wsRef.current = null
      }
    }
  // sessionId 是唯一依赖，其他状态通过 ref 追踪
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  return { connectionState, messages, checkpointState, sessionEnded, teachingMode, sessionReady }
}
