// frontend/src/apis/observation.ts
import { api } from './base'
import type {
  CheckpointStateData,
  ObservationConfigPayload,
  ObservationStartResponse,
} from '../types/observation'

/** 单个检查点（对应后端 Checkpoint schema） */
export interface CheckpointItem {
  title: string
  key_point: string
  checkpoint_question: string
  state: string
}

/** 检查点计划（对应后端 CheckpointPlan schema） */
export interface CheckpointPlanData {
  topic: string
  teaching_mode: string
  checkpoints: CheckpointItem[]
  current_index: number
}

/**
 * 获取会话的检查点计划.
 *
 * @param sessionId 会话 ID
 * @returns 检查点计划数据（包含所有检查点标题）
 */
export async function getCheckpointPlan(
  sessionId: number,
): Promise<CheckpointPlanData> {
  const { data } = await api.get<CheckpointPlanData>(
    `/checkpoint-plans/${sessionId}`,
  )
  return data
}

/**
 * 获取检查点进度（页面加载时调用）.
 *
 * @param sessionId 会话 ID
 * @returns 当前检查点进度数据
 */
export async function getCheckpointProgress(
  sessionId: number,
): Promise<CheckpointStateData> {
  const { data } = await api.get<CheckpointStateData>(
    `/observation/${sessionId}/checkpoint-progress`,
  )
  return data
}

/** 启动观察模式会话 */
export async function startObservation(
  config: ObservationConfigPayload,
): Promise<ObservationStartResponse> {
  const { data } = await api.post<ObservationStartResponse>(
    '/observation/start',
    config,
  )
  return data
}

/** 学生个体指标 */
export interface StudentMetrics {
  student_name: string
  level: string
  attitude: string
  learning_ability: number
  knowledge_gain: number
  final_knowledge_level: number
  message_count: number
  questions_asked: number
  learned_concepts_count: number
}

/** 分析报告响应 */
export interface AnalysisReport {
  session_id: number
  topic: string
  teaching_mode: string
  duration_seconds: number | null
  total_checkpoints: number
  completed_checkpoints: number
  total_messages: number
  teacher_message_count: number
  student_message_count: number
  interaction_frequency: number
  student_participation_rate: number
  average_knowledge_gain: number
  average_correct_rate: number
  student_metrics: StudentMetrics[]
}

/**
 * 获取观察模式分析报告.
 *
 * @param sessionId 会话 ID
 * @returns 分析报告数据
 * @throws 当会话不存在时抛出错误
 */
export async function getAnalysisReport(sessionId: number): Promise<AnalysisReport> {
  const { data } = await api.get<AnalysisReport>(
    `/observation/${sessionId}/report`,
  )
  return data
}
