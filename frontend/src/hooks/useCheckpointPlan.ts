// frontend/src/hooks/useCheckpointPlan.ts
import { useReducer, useEffect } from 'react'
import { getCheckpointPlan } from '../apis/observation'
import type { CheckpointPlanData } from '../apis/observation'

/** 检查点计划加载状态 */
interface PlanState {
  plan: CheckpointPlanData | null
  loading: boolean
  error: string | null
}

/** fetchReducer 的 action 类型 */
type PlanAction =
  | { type: 'fetch' }
  | { type: 'success'; payload: CheckpointPlanData }
  | { type: 'error'; payload: string }

/** 检查点计划加载的 reducer，使用 useReducer 避免在 useEffect 中调用 setState */
function planReducer(state: PlanState, action: PlanAction): PlanState {
  switch (action.type) {
    case 'fetch':
      return { plan: null, loading: true, error: null }
    case 'success':
      return { plan: action.payload, loading: false, error: null }
    case 'error':
      return { ...state, loading: false, error: action.payload }
  }
}

/**
 * 获取会话的检查点计划（包含所有检查点标题）.
 *
 * 当 enabled 变为 true 时自动拉取，用于侧边栏渲染完整检查点列表。
 * 如果拉取失败，保留 error 信息但不会重试。
 *
 * @param sessionId 会话 ID
 * @param enabled 是否拉取（实时模式等 sessionReady，回顾模式直接启用）
 * @returns 包含 plan、loading、error 的状态对象
 */
export function useCheckpointPlan(
  sessionId: number,
  enabled: boolean,
) {
  const [state, dispatch] = useReducer(planReducer, {
    plan: null,
    loading: false,
    error: null,
  })

  useEffect(() => {
    if (!enabled || sessionId <= 0) return

    let cancelled = false
    dispatch({ type: 'fetch' })

    getCheckpointPlan(sessionId)
      .then((data) => {
        if (!cancelled) dispatch({ type: 'success', payload: data })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          dispatch({
            type: 'error',
            payload: err instanceof Error ? err.message : '加载失败',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [sessionId, enabled])

  return state
}
