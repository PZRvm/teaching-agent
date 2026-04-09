// frontend/src/hooks/useWebSocket.ts
// 观察模式 WebSocket wrapper —— 复用 useWebSocketBase，保持向后兼容
import { useWebSocketBase } from './useWebSocketBase'
import type { UseWebSocketBaseReturn } from './useWebSocketBase'

/** 观察模式 WebSocket hook（只读） */
export function useWebSocket(sessionId: number): UseWebSocketBaseReturn {
  return useWebSocketBase(sessionId)
}
