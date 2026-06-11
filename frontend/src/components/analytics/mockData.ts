// 三种教学模式配色
export const COLORS = {
  didactic: '#3B82F6',
  heuristic: '#A855F7',
  discussion: '#22C55E',
} as const

export const MODE_LABELS = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
} as const

export type Mode = keyof typeof COLORS

// === 总览数据 ===

export const overviewScores = {
  didactic: { overall: 72.5, learning: 70, participation: 55, satisfaction: 65 },
  heuristic: { overall: 85.3, learning: 82, participation: 78, satisfaction: 88 },
  discussion: { overall: 91.8, learning: 93, participation: 95, satisfaction: 90 },
}

export const overviewRadar = {
  indicators: ['知识掌握', '思维能力', '参与度', '满意度', '课堂氛围'],
  didactic: [72, 58, 55, 65, 60],
  heuristic: [85, 78, 78, 88, 82],
  discussion: [93, 90, 95, 90, 92],
}

export const overviewTrend = {
  checkpoints: ['检查点1', '检查点2', '检查点3', '检查点4', '检查点5'],
  didactic: [65, 70, 72, 74, 75],
  heuristic: [72, 78, 84, 87, 88],
  discussion: [78, 85, 90, 92, 95],
}

// === 学习成效数据 ===

export const learningEffectAccuracy = {
  checkpoints: ['检查点1', '检查点2', '检查点3', '检查点4', '检查点5'],
  didactic: [68, 72, 70, 74, 75],
  heuristic: [75, 80, 83, 85, 87],
  discussion: [80, 88, 92, 94, 95],
}

export const learningEffectGrades = {
  didactic: { A: 15, B: 40, C: 35, D: 10, avg: 'B-' },
  heuristic: { A: 35, B: 40, C: 20, D: 5, avg: 'B+' },
  discussion: { A: 55, B: 30, C: 12, D: 3, avg: 'A-' },
}

export const learningEffectMastery = {
  checkpoints: ['检查点1', '检查点2', '检查点3', '检查点4', '检查点5'],
  didactic: [55, 60, 65, 68, 70],
  heuristic: [65, 72, 80, 85, 88],
  discussion: [72, 82, 90, 93, 95],
}

// === 学生参与度数据 ===

export const participationQA = {
  modes: ['灌输式', '启发式', '讨论式'],
  questions: [12, 35, 68],
  answers: [45, 78, 95],
}

export const participationType = {
  didactic: { active: 20, passive: 40, bystander: 40 },
  heuristic: { active: 45, passive: 35, bystander: 20 },
  discussion: { active: 72, passive: 20, bystander: 8 },
}

export const participationTrend = {
  checkpoints: ['检查点1', '检查点2', '检查点3', '检查点4', '检查点5'],
  didactic: [50, 48, 45, 52, 55],
  heuristic: [65, 72, 78, 82, 85],
  discussion: [80, 85, 92, 95, 98],
}

// === 学生满意度数据 ===

export const satisfactionLevels = {
  didactic: { verySatisfied: 18, satisfied: 35, neutral: 32, dissatisfied: 15 },
  heuristic: { verySatisfied: 40, satisfied: 38, neutral: 17, dissatisfied: 5 },
  discussion: { verySatisfied: 58, satisfied: 30, neutral: 10, dissatisfied: 2 },
}

export const satisfactionRadar = {
  indicators: ['内容质量', '互动体验', '难度适中性', '节奏感', '收获感'],
  didactic: [70, 45, 65, 55, 68],
  heuristic: [82, 78, 80, 75, 85],
  discussion: [90, 92, 88, 82, 95],
}

export const satisfactionNPS = {
  modes: ['灌输式', '启发式', '讨论式'],
  scores: [28, 62, 78],
}
