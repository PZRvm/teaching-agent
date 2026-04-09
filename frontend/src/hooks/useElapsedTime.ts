// frontend/src/hooks/useElapsedTime.ts
/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useState } from 'react'

/** 将秒数格式化为 MM:SS */
function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

/** 已进行时间计时器 hook，每秒更新一次 */
export function useElapsedTime(running: boolean): string {
  // 当 running 变化时，用 derived state 计算初始值
  const [seconds, setSeconds] = useState(0)

  useEffect(() => {
    if (!running) {
      return
    }

    // 当开始运行时，重置为 0
    setSeconds(0)

    const interval = setInterval(() => {
      setSeconds((prev) => prev + 1)
    }, 1_000)

    return () => clearInterval(interval)
  }, [running])

  return formatTime(seconds)
}
