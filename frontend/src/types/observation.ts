// frontend/src/types/observation.ts

/** 教学模式 */
export type TeachingMode = 'didactic' | 'heuristic' | 'discussion'

/** 教学模式中文名映射 */
export const TEACHING_MODE_LABELS: Record<TeachingMode, string> = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
}

/** 学生水平 */
export type StudentLevel = 'excellent' | 'average' | 'basic'

/** 学生态度 */
export type StudentAttitude = 'active' | 'neutral' | 'passive'

/** 学生配置文件（对应后端 StudentProfile） */
export interface StudentProfile {
  name: string
  gender?: string | null
  level: StudentLevel
  attitude: StudentAttitude
  learning_ability: number
  background?: string | null
  special_traits?: string[]
}

/** 学生水平枚举（用于选择器） */
export const STUDENT_LEVEL_OPTIONS = [
  { value: 'excellent' as StudentLevel, label: '优秀', color: '#E3F2FD' },
  { value: 'average' as StudentLevel, label: '中等', color: '#FFF9C4' },
  { value: 'basic' as StudentLevel, label: '基础', color: '#FFECB3' },
] as const

/** 学生态度枚举（用于选择器） */
export const STUDENT_ATTITUDE_OPTIONS = [
  { value: 'active' as StudentAttitude, label: '积极', color: '#C8E6C9' },
  { value: 'neutral' as StudentAttitude, label: '中性', color: '#FFF9C4' },
  { value: 'passive' as StudentAttitude, label: '消极', color: '#FFCDD2' },
] as const

/** 学生创建方式 */
export type StudentCreateSource = 'manual' | 'random' | 'json'

/** 随机班级生成配置 */
export interface RandomClassConfig {
  total_students: number
  level_distribution: { [key: string]: number }
  attitude_distribution: { [key: string]: number }
  random_seed?: number | null
}

/** 学生创建请求（对应后端 StudentCreateRequest） */
export interface StudentCreateRequest {
  source: StudentCreateSource
  manual_students?: StudentProfile[]
  random_config?: RandomClassConfig
  json_data?: string
}

/** 观察模式配置（对应后端 ObservationConfig） */
export interface ObservationConfigPayload {
  topic: string
  teaching_mode: TeachingMode
  checkpoint_count: number
  students: StudentProfile[]
}

/** 观察模式启动响应（对应后端 ObservationStartResponse） */
export interface ObservationStartResponse {
  session_id: number
  status: string
}

/** WebSocket 消息类型 */
export type WsMessageType =
  | 'connected'
  | 'message'
  | 'checkpoint_state_change'
  | 'session_state'
  | 'session_end'
  | 'error'
  | 'pong'

/** WebSocket 消息基类 */
export interface WsEvent {
  type: WsMessageType
  session_id: number
}

/** WebSocket 连接确认事件 */
export interface WsConnectedEvent extends WsEvent {
  type: 'connected'
  mode?: 'observation' | 'teacher'
  ready?: boolean // orchestrator 是否已就绪
}

/** WebSocket 消息事件（教师讲授/学生回答等） */
export interface WsMessageEvent extends WsEvent {
  type: 'message'
  sender: string
  message_type: string
  content: string
  receiver?: string
}

/** WebSocket 检查点状态变更事件 */
export interface WsCheckpointStateEvent extends WsEvent {
  type: 'checkpoint_state_change'
  index: number
  checkpoint: {
    title: string
    state: string
    key_point: string
  }
  progress: {
    current: number
    total: number
    completed: number
  }
}

/** WebSocket 会话状态事件 */
export interface WsSessionStateEvent extends WsEvent {
  type: 'session_state'
  teaching_mode: string
  status?: string // 'initializing' | 'running' | 'error' | 'ended'
  phase?: string
  checkpoint_index?: number
  total_checkpoints?: number
  message?: string // 错误消息（当 status='error' 时）
}

/** WebSocket 会话结束事件 */
export interface WsSessionEndEvent extends WsEvent {
  type: 'session_end'
  reason: string
}

/** WebSocket 错误事件 */
export interface WsErrorEvent extends WsEvent {
  type: 'error'
  message: string
}

/** 所有 WebSocket 事件联合类型 */
export type WsEventUnion =
  | WsConnectedEvent
  | WsMessageEvent
  | WsCheckpointStateEvent
  | WsSessionStateEvent
  | WsSessionEndEvent
  | WsErrorEvent
  | { type: 'pong' }

/** 检查点状态 */
export type CheckpointState = 'pending' | 'teaching' | 'questions' | 'complete'

/** 检查点信息 */
export interface CheckpointInfo {
  title: string
  state: CheckpointState
  key_point: string
}

/** 检查点进度 */
export interface CheckpointProgress {
  current: number
  total: number
  completed: number
}

/** 检查点状态数据（从 WebSocket 提取） */
export interface CheckpointStateData {
  index: number
  checkpoint: CheckpointInfo
  progress: CheckpointProgress
}
