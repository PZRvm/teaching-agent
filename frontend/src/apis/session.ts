// frontend/src/apis/session.ts
import { api } from './base'

/** 历史消息（来自 GET /sessions/{id}/messages） */
export interface SessionMessage {
  id: number
  session_id: number
  sender: string
  message_type: string
  content: string
  receiver: string
  timestamp: string // ISO 8601
}

/** 获取会话历史消息 */
export async function getSessionMessages(
  sessionId: number,
): Promise<SessionMessage[]> {
  const { data } = await api.get<SessionMessage[]>(
    `/sessions/${sessionId}/messages`,
  )
  return data
}
