// frontend/tests/hooks/useWebSocketBase.test.ts
import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import type { WsEventUnion } from '../../src/types/observation'

// 模块级实例追踪，用于在测试中获取创建的 WebSocket 实例
let lastCreatedWs: MockWebSocket | null = null

// WebSocket mock 类
class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3
  static CONNECTING = 0
  readyState = MockWebSocket.CONNECTING
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  send = vi.fn()
  close = vi.fn()

  constructor(public url: string) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    lastCreatedWs = this
  }

  // 模拟连接成功
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.()
  }

  // 模拟收到消息
  simulateMessage(data: WsEventUnion) {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  // 模拟连接关闭
  simulateClose() {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.()
  }
}

// 保存原始 WebSocket
const OriginalWebSocket = globalThis.WebSocket

beforeEach(() => {
  lastCreatedWs = null
  vi.useFakeTimers()
  // 替换全局 WebSocket
  globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket
})

afterEach(() => {
  vi.useRealTimers()
  globalThis.WebSocket = OriginalWebSocket
})

// 延迟导入 hook（在 WebSocket mock 设置完成后）
async function getHook() {
  return (await import('../../src/hooks/useWebSocketBase')).useWebSocketBase
}

describe('useWebSocketBase', () => {
  it('initializes with connecting state', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    expect(result.current.connectionState).toBe('connecting')
  })

  it('transitions to connected state on open', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))

    // 获取创建的 WebSocket 实例
    const createdWs = lastCreatedWs!
    act(() => createdWs.simulateOpen())

    expect(result.current.connectionState).toBe('connected')
  })

  it('stores received messages in messages array', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    act(() =>
      createdWs.simulateMessage({
        type: 'message',
        session_id: 1,
        sender: 'teacher',
        message_type: 'lecture',
        content: '今天我们学习Python变量...',
      }),
    )

    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0].content).toBe('今天我们学习Python变量...')
  })

  it('updates checkpointState on checkpoint_state_change event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    act(() =>
      createdWs.simulateMessage({
        type: 'checkpoint_state_change',
        session_id: 1,
        index: 0,
        checkpoint: { title: 'Python简介', state: 'teaching', key_point: '基础语法' },
        progress: { current: 1, total: 5, completed: 0 },
      }),
    )

    expect(result.current.checkpointState).not.toBeNull()
    expect(result.current.checkpointState!.checkpoint.title).toBe('Python简介')
    expect(result.current.checkpointState!.progress.total).toBe(5)
  })

  it('sets sessionEnded to true on session_end event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    expect(result.current.sessionEnded).toBe(false)

    act(() =>
      createdWs.simulateMessage({
        type: 'session_end',
        session_id: 1,
        reason: 'all_checkpoints_completed',
      }),
    )

    expect(result.current.sessionEnded).toBe(true)
  })

  it('updates teachingMode from session_state event', async () => {
    const useWebSocketBase = await getHook()
    const { result } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    expect(result.current.teachingMode).toBeNull()

    act(() =>
      createdWs.simulateMessage({
        type: 'session_state',
        session_id: 1,
        teaching_mode: 'heuristic',
        phase: 'teaching',
        checkpoint_index: 0,
        total_checkpoints: 5,
      }),
    )

    expect(result.current.teachingMode).toBe('heuristic')
  })

  it('closes WebSocket on unmount', async () => {
    const useWebSocketBase = await getHook()
    const { unmount } = renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())
    unmount()

    expect(createdWs.close).toHaveBeenCalled()
  })

  it('sends ping heartbeat every 30 seconds', async () => {
    const useWebSocketBase = await getHook()
    renderHook(() => useWebSocketBase(1))
    const createdWs = lastCreatedWs!

    act(() => createdWs.simulateOpen())

    // 快进 30 秒
    act(() => vi.advanceTimersByTime(30_000))
    expect(createdWs.send).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }))

    // 再快进 30 秒
    act(() => vi.advanceTimersByTime(30_000))
    expect(createdWs.send).toHaveBeenCalledTimes(2)
  })
})
