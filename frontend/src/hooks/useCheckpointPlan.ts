// frontend/src/hooks/useCheckpointPlan.ts
import { useReducer, useEffect } from 'react'
import { getCheckpointPlan } from '../apis/observation'
import type { CheckpointPlanData } from '../apis/observation'

interface PlanState {
  plan: CheckpointPlanData | null
  loading: boolean
  error: string | null
}

type PlanAction =
  | { type: 'fetch' }
  | { type: 'success'; payload: CheckpointPlanData }
  | { type: 'error'; payload: string }

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
 * 获取会话的检查点计划（包含所有检查点标题）。
 *
 * 当 sessionReady 变为 true 时自动拉取，用于侧边栏渲染完整检查点列表。
 */
export function useCheckpointPlan(
  sessionId: number,
  sessionReady: boolean,
) {
  const [state, dispatch] = useReducer(planReducer, {
    plan: null,
    loading: false,
    error: null,
  })

  useEffect(() => {
    if (!sessionReady || sessionId <= 0) return

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
  }, [sessionId, sessionReady])

  return state
}
