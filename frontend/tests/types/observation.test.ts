// frontend/tests/types/observation.test.ts
import { describe, expect, it } from 'vitest'
import {
  type StudentProfile,
  type ObservationConfigPayload,
  type WsMessageEvent,
  type WsCheckpointStateEvent,
  type WsSessionEndEvent,
  type CheckpointState,
  type CheckpointStateData,
  TEACHING_MODE_LABELS,
} from '../../src/types/observation'

describe('observation types', () => {
  it('exports TEACHING_MODE_LABELS with correct labels', () => {
    expect(TEACHING_MODE_LABELS.didactic).toBe('灌输式')
    expect(TEACHING_MODE_LABELS.heuristic).toBe('启发式')
    expect(TEACHING_MODE_LABELS.discussion).toBe('讨论式')
  })

  it('TEACHING_MODE_LABELS has exactly 3 entries', () => {
    expect(Object.keys(TEACHING_MODE_LABELS).length).toBe(3)
  })

  it('allows constructing valid StudentProfile objects', () => {
    const student: StudentProfile = {
      name: '张三',
      level: 'excellent',
      attitude: 'active',
      learning_ability: 8,
    }
    expect(student.name).toBe('张三')
    expect(student.learning_ability).toBe(8)
  })

  it('allows constructing valid ObservationConfigPayload', () => {
    const config: ObservationConfigPayload = {
      topic: 'Python变量与数据类型',
      teaching_mode: 'heuristic',
      checkpoint_count: 5,
      students: [{ name: '张三', level: 'average', attitude: 'neutral', learning_ability: 5 }],
    }
    expect(config.topic).toBe('Python变量与数据类型')
    expect(config.students).toHaveLength(1)
  })

  it('allows constructing valid WsMessageEvent', () => {
    const event: WsMessageEvent = {
      type: 'message',
      session_id: 1,
      sender: 'teacher',
      message_type: 'lecture',
      content: '今天我们学习Python变量...',
    }
    expect(event.type).toBe('message')
    expect(event.sender).toBe('teacher')
  })

  it('allows constructing valid WsCheckpointStateEvent', () => {
    const event: WsCheckpointStateEvent = {
      type: 'checkpoint_state_change',
      session_id: 1,
      index: 0,
      checkpoint: { title: 'Python简介', state: 'teaching', key_point: 'Python基础语法' },
      progress: { current: 1, total: 5, completed: 0 },
    }
    expect(event.checkpoint.title).toBe('Python简介')
    expect(event.progress.total).toBe(5)
  })

  it('allows constructing valid WsSessionEndEvent', () => {
    const event: WsSessionEndEvent = {
      type: 'session_end',
      session_id: 1,
      reason: 'all_checkpoints_completed',
    }
    expect(event.reason).toBe('all_checkpoints_completed')
  })

  it('CheckpointState accepts valid states', () => {
    const states: CheckpointState[] = ['pending', 'teaching', 'questions', 'complete']
    expect(states).toHaveLength(4)
  })

  it('CheckpointStateData matches expected shape', () => {
    const data: CheckpointStateData = {
      index: 0,
      checkpoint: { title: 'Test', state: 'pending', key_point: 'test' },
      progress: { current: 1, total: 3, completed: 0 },
    }
    expect(data.index).toBe(0)
    expect(data.progress.current).toBe(1)
  })
})
