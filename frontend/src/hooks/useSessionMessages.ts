// frontend/src/hooks/useSessionMessages.ts
import { useReducer, useEffect, useMemo } from 'react'
import { getSessionMessages } from '../apis/session'
import type { SessionMessage } from '../apis/session'
import type { WsMessageEvent } from '../types/observation'

/** 统一显示消息（历史 + 实时） */
export interface DisplayMessage {
  id?: number
  sender: string
  message_type: string
  content: string
  receiver: string
  timestamp?: string
}

export interface UseSessionMessagesReturn {
  messages: DisplayMessage[]
  loading: boolean
  error: string | null
}

/** 历史消息拉取状态 */
interface FetchState {
  history: DisplayMessage[]
  loading: boolean
  error: string | null
}

/** fetchReducer 的 action 类型 */
type FetchAction =
  | { type: 'fetch' }
  | { type: 'success'; payload: DisplayMessage[] }
  | { type: 'error'; payload: string }

/** 历史消息拉取的 reducer，使用 useReducer 避免在 useEffect 中调用 setState */
function fetchReducer(state: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case 'fetch':
      return { history: [], loading: true, error: null }
    case 'success':
      return { history: action.payload, loading: false, error: null }
    case 'error':
      // 保留已有的 history，避免错误后清空已加载的数据
      return { ...state, loading: false, error: action.payload }
  }
}

/** 将后端 SessionMessage 转换为前端 DisplayMessage */
function historyToDisplay(msg: SessionMessage): DisplayMessage {
  return {
    id: msg.id,
    sender: msg.sender,
    message_type: msg.message_type,
    content: msg.content,
    receiver: msg.receiver,
    timestamp: msg.timestamp,
  }
}

/** 将 WebSocket 实时消息转换为 DisplayMessage，receiver 缺省为 'all' */
function wsToDisplay(msg: WsMessageEvent): DisplayMessage {
  return {
    sender: msg.sender,
    message_type: msg.message_type,
    content: msg.content,
    receiver: msg.receiver ?? 'all',
    timestamp: msg.timestamp,
  }
}

/**
 * 判断 WebSocket 消息是否与已有消息重复.
 *
 * 去重策略：
 * 1. 如果 WS 消息的 timestamp 严格大于最后一条历史消息的时间戳，
 *    说明一定是新消息，直接返回 false（非重复）。
 * 2. 否则在最近 5 条消息中做三字段匹配（sender + message_type + content），
 *    任一匹配即视为重复。
 */
function isDuplicate(
  wsMsg: DisplayMessage,
  existingMsgs: DisplayMessage[],
): boolean {
  if (existingMsgs.length === 0) return false

  const lastTimestamp = existingMsgs[existingMsgs.length - 1]?.timestamp
  if (wsMsg.timestamp && lastTimestamp) {
    const wsTime = new Date(wsMsg.timestamp).getTime()
    const lastTime = new Date(lastTimestamp).getTime()
    if (!isNaN(wsTime) && !isNaN(lastTime) && wsTime > lastTime) {
      return false
    }
  }

  const checkCount = Math.min(existingMsgs.length, 5)
  for (let i = existingMsgs.length - 1; i >= existingMsgs.length - checkCount; i--) {
    if (i < 0) break
    const existing = existingMsgs[i]
    if (
      existing.sender === wsMsg.sender &&
      existing.message_type === wsMsg.message_type &&
      existing.content === wsMsg.content
    ) {
      return true
    }
  }
  return false
}

/**
 * 合并历史消息和 WebSocket 实时消息的 hook.
 *
 * 工作流程：
 * 1. sessionId 变化时，通过 REST API 拉取历史消息
 * 2. WebSocket 实时消息到达时，与历史消息去重后追加到末尾
 * 3. 返回合并后的消息列表、加载状态和错误信息
 *
 * @param sessionId 会话 ID，无效时不拉取
 * @param wsMessages 来自 useWebSocketBase 的实时消息数组
 */
export function useSessionMessages(
  sessionId: number,
  wsMessages: WsMessageEvent[],
): UseSessionMessagesReturn {
  const [state, dispatch] = useReducer(fetchReducer, {
    history: [],
    loading: sessionId > 0,
    error: null,
  })

  // 拉取历史消息（仅在 sessionId 变化时触发）
  useEffect(() => {
    if (!sessionId || sessionId <= 0) {
      return
    }

    let cancelled = false
    dispatch({ type: 'fetch' })

    getSessionMessages(sessionId)
      .then((msgs) => {
        console.log(msgs)
        if (!cancelled) {
          dispatch({ type: 'success', payload: msgs.map(historyToDisplay) })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: 'error',
            payload: err instanceof Error ? err.message : '加载历史消息失败',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [sessionId])

  // 合并历史消息与实时消息，去重后返回
  const messages = useMemo(() => {
    const result = [...state.history]
    for (const wsMsg of wsMessages) {
      const display = wsToDisplay(wsMsg)
      if (!isDuplicate(display, result)) {
        result.push(display)
      }
    }
    return result
  }, [state.history, wsMessages])

  return { messages, loading: state.loading, error: state.error }
}
