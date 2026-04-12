// frontend/src/hooks/useElapsedTime.ts
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from 'react'

/** 将秒数格式化为 MM:SS */
function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

/**
 * 已进行时间计时器 hook.
 *
 * 从 running 变为 true 时开始计时，每秒递增一次。
 * running 变为 false 时暂停，再次变为 true 时重置为 00:00。
 *
 * @param running 是否正在计时
 * @returns 格式化后的时间字符串，格式为 MM:SS
 */
export function useElapsedTime(running: boolean): string {
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    if (!running) {
      return
    }

    // 开始计时，重置计数器
    setSeconds(0)

    const interval = setInterval(() => {
      setSeconds((prev) => prev + 1)
    }, 1_000)

    return () => clearInterval(interval)
  }, [running])

  return formatTime(seconds)
}
