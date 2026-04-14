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

/** 会话检查点进度 */
export interface CheckpointProgress {
  total: number
  completed: number
  current_index: number
}

/** 会话列表项 */
export interface SessionSummary {
  id: number
  topic: string
  teaching_mode: string
  status: string
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  student_count: number
  checkpoint_progress: CheckpointProgress | null
}

/** 获取历史会话列表 */
export async function getSessionList(): Promise<SessionSummary[]> {
  const { data } = await api.get<SessionSummary[]>('/sessions/')
  return data
}
