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

interface FetchState {
  history: DisplayMessage[]
  loading: boolean
  error: string | null
}

type FetchAction =
  | { type: 'fetch' }
  | { type: 'success'; payload: DisplayMessage[] }
  | { type: 'error'; payload: string }

function fetchReducer(_state: FetchState, action: FetchAction): FetchState {
  switch (action.type) {
    case 'fetch':
      return { history: [], loading: true, error: null }
    case 'success':
      return { history: action.payload, loading: false, error: null }
    case 'error':
      return { history: [], loading: false, error: action.payload }
  }
}

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

function wsToDisplay(msg: WsMessageEvent): DisplayMessage {
  return {
    sender: msg.sender,
    message_type: msg.message_type,
    content: msg.content,
    receiver: msg.receiver ?? 'all',
    timestamp: msg.timestamp,
  }
}

function isDuplicate(
  wsMsg: DisplayMessage,
  existingMsgs: DisplayMessage[],
): boolean {
  if (existingMsgs.length === 0) return false

  const lastTimestamp = existingMsgs[existingMsgs.length - 1]?.timestamp
  if (wsMsg.timestamp && lastTimestamp && wsMsg.timestamp > lastTimestamp) {
    return false
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

export function useSessionMessages(
  sessionId: number,
  wsMessages: WsMessageEvent[],
): UseSessionMessagesReturn {
  const [state, dispatch] = useReducer(fetchReducer, {
    history: [],
    loading: sessionId > 0,
    error: null,
  })

  useEffect(() => {
    if (!sessionId || sessionId <= 0) {
      return
    }

    let cancelled = false
    dispatch({ type: 'fetch' })

    getSessionMessages(sessionId)
      .then((msgs) => {
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
