/** 将秒数格式化为可读时长，如 "25分30秒"、"1小时15分" */
export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)

  if (h > 0) {
    const parts = [`${h}小时`]
    if (m > 0) parts.push(`${m}分`)
    return parts.join('')
  }
  if (m > 0) {
    const parts = [`${m}分`]
    if (s > 0) parts.push(`${s}秒`)
    return parts.join('')
  }
  return `${s}秒`
}

/** 将 ISO 8601 日期字符串格式化为 "YYYY年M月D日" */
export function formatDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

/** 将 ISO 8601 时间字符串格式化为 "HH:mm" */
export function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
