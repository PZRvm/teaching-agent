// frontend/src/hooks/useCheckpointProgress.ts
import { useReducer, useEffect, useRef } from 'react'
import { getCheckpointProgress } from '../apis/observation'
import type { CheckpointStateData } from '../types/observation'

/** 检查点进度加载状态 */
interface ProgressState {
  progress: CheckpointStateData | null
  loading: boolean
}

/** fetchReducer 的 action 类型 */
type ProgressAction =
  | { type: 'fetch' }
  | { type: 'success'; payload: CheckpointStateData }
  | { type: 'done' }

/** 检查点进度加载的 reducer */
function progressReducer(state: ProgressState, action: ProgressAction): ProgressState {
  switch (action.type) {
    case 'fetch':
      return { progress: null, loading: true }
    case 'success':
      return { progress: action.payload, loading: false }
    case 'done':
      return { ...state, loading: false }
  }
}

export interface UseCheckpointProgressReturn {
  progress: CheckpointStateData | null
  loading: boolean
}

/**
 * 页面加载时一次性获取检查点进度.
 *
 * 用于在 WebSocket 连接建立前或断连后提供初始检查点状态。
 * WebSocket 的实时更新会覆盖此值（通过 ?? 合并）。
 *
 * @param sessionId 会话 ID
 * @returns 检查点进度数据和加载状态
 */
export function useCheckpointProgress(
  sessionId: number,
): UseCheckpointProgressReturn {
  const [state, dispatch] = useReducer(progressReducer, {
    progress: null,
    loading: sessionId > 0,
  })
  const fetchedRef = useRef(false)

  useEffect(() => {
    if (sessionId <= 0 || fetchedRef.current) return

    fetchedRef.current = true
    dispatch({ type: 'fetch' })

    getCheckpointProgress(sessionId)
      .then((data) => {
        dispatch({ type: 'success', payload: data })
      })
      .catch(() => {
        dispatch({ type: 'done' })
      })
  }, [sessionId])

  return { progress: state.progress, loading: state.loading }
}
