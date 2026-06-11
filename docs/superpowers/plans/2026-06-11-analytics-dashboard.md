# 答辩数据分析页面实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建答辩用的教学智能体效果分析页面，通过 ECharts 图表展示三种教学模式（灌输式、启发式、讨论式）在多个维度上的教学效果差异。

**Architecture:** 纯前端页面，新增 `/analytics` 路由。主页面 `AnalyticsDashboard` 管理 Tab 切换和顶部指标卡片，四个子 Tab 组件各自渲染 3 个 ECharts 图表。所有数据来自 `mockData.ts` 静态模块。使用 `echarts-for-react` 封装 ECharts 实例。

**Tech Stack:** React 19, React Router 7, styled-components, ECharts 5, echarts-for-react 3

---

## 文件结构

```
frontend/src/
├── views/
│   └── AnalyticsDashboard.tsx       # 主页面（Tab 切换 + 指标卡片）
├── components/
│   └── analytics/
│       ├── OverviewTab.tsx           # 总览 Tab（柱状图 + 雷达图 + 折线图）
│       ├── LearningEffectTab.tsx     # 学习成效 Tab（柱状图 + 饼图 + 折线图）
│       ├── ParticipationTab.tsx      # 学生参与度 Tab（柱状图 + 饼图 + 折线图）
│       ├── SatisfactionTab.tsx       # 学生满意度 Tab（饼图 + 雷达图 + 柱状图）
│       └── mockData.ts              # 静态模拟数据
├── App.tsx                          # 新增 /analytics 路由
```

---

### Task 1: 安装依赖

- [ ] **Step 1: 安装 echarts 和 echarts-for-react**

```bash
cd frontend
npm install echarts echarts-for-react
```

- [ ] **Step 2: 验证安装成功**

```bash
cd frontend
npm ls echarts echarts-for-react
```

Expected: 两个包均出现在依赖树中。

---

### Task 2: 创建模拟数据模块

**Files:**
- Create: `frontend/src/components/analytics/mockData.ts`

- [ ] **Step 1: 创建 mockData.ts**

```typescript
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
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

---

### Task 3: 创建总览 Tab 组件

**Files:**
- Create: `frontend/src/components/analytics/OverviewTab.tsx`

- [ ] **Step 1: 创建 OverviewTab.tsx**

```tsx
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, RadarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import styled from 'styled-components'
import {
  COLORS,
  MODE_LABELS,
  overviewScores,
  overviewRadar,
  overviewTrend,
} from './mockData'

echarts.use([
  BarChart, LineChart, RadarChart,
  GridComponent, TooltipComponent, LegendComponent, RadarComponent,
  CanvasRenderer,
])

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  .chart-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }

  .chart-card-full {
    grid-column: 1 / -1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }
`

const modes = Object.keys(COLORS) as (keyof typeof COLORS)[]

const barOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  xAxis: {
    type: 'category' as const,
    data: ['学习成效', '学生参与度', '教学效率', '学生满意度'],
  },
  yAxis: { type: 'value' as const, max: 100 },
  series: modes.map((m) => ({
    name: MODE_LABELS[m],
    type: 'bar' as const,
    data: [
      overviewScores[m].learning,
      overviewScores[m].participation,
      overviewScores[m].participation * 0.9,
      overviewScores[m].satisfaction,
    ],
    itemStyle: { color: COLORS[m], borderRadius: [4, 4, 0, 0] },
  })),
}

const radarOption = {
  tooltip: {},
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  radar: {
    indicator: overviewRadar.indicators.map((name) => ({ name, max: 100 })),
  },
  series: [
    {
      type: 'radar' as const,
      data: modes.map((m) => ({
        name: MODE_LABELS[m],
        value: overviewRadar[m],
        lineStyle: { color: COLORS[m] },
        itemStyle: { color: COLORS[m] },
        areaStyle: { color: COLORS[m], opacity: 0.1 },
      })),
    },
  ],
}

const lineOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  xAxis: { type: 'category' as const, data: overviewTrend.checkpoints },
  yAxis: { type: 'value' as const, min: 50, max: 100 },
  series: modes.map((m) => ({
    name: MODE_LABELS[m],
    type: 'line' as const,
    data: overviewTrend[m],
    smooth: true,
    lineStyle: { color: COLORS[m], width: 2 },
    itemStyle: { color: COLORS[m] },
  })),
}

export default function OverviewTab() {
  return (
    <ChartGrid>
      <div className="chart-card">
        <div className="chart-title">四维度均分对比</div>
        <ReactEChartsCore
          echarts={echarts}
          option={barOption}
          style={{ height: 300 }}
        />
      </div>
      <div className="chart-card">
        <div className="chart-title">综合能力画像</div>
        <ReactEChartsCore
          echarts={echarts}
          option={radarOption}
          style={{ height: 300 }}
        />
      </div>
      <div className="chart-card-full">
        <div className="chart-title">各检查点阶段效果趋势</div>
        <ReactEChartsCore
          echarts={echarts}
          option={lineOption}
          style={{ height: 300 }}
        />
      </div>
    </ChartGrid>
  )
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

---

### Task 4: 创建学习成效 Tab 组件

**Files:**
- Create: `frontend/src/components/analytics/LearningEffectTab.tsx`

- [ ] **Step 1: 创建 LearningEffectTab.tsx**

```tsx
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import styled from 'styled-components'
import {
  COLORS,
  MODE_LABELS,
  learningEffectAccuracy,
  learningEffectGrades,
  learningEffectMastery,
} from './mockData'

echarts.use([
  BarChart, LineChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent,
  CanvasRenderer,
])

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  .chart-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }

  .chart-card-full {
    grid-column: 1 / -1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }
`

const PieRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-top: 4px;

  .pie-label {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
  }
`

const modes = Object.keys(COLORS) as (keyof typeof COLORS)[]
const gradeLabels = ['优秀(A)', '良好(B)', '及格(C)', '不及格(D)']
const gradeColors = ['#22C55E', '#3B82F6', '#F59E0B', '#EF4444']

// 柱状图：各检查点正确率
const accuracyOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  xAxis: { type: 'category' as const, data: learningEffectAccuracy.checkpoints },
  yAxis: { type: 'value' as const, max: 100, axisLabel: { formatter: '{value}%' } },
  series: modes.map((m) => ({
    name: MODE_LABELS[m],
    type: 'bar' as const,
    data: learningEffectAccuracy[m],
    itemStyle: { color: COLORS[m], borderRadius: [4, 4, 0, 0] },
  })),
}

// 折线图：知识掌握度趋势
const masteryOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  xAxis: { type: 'category' as const, data: learningEffectMastery.checkpoints },
  yAxis: { type: 'value' as const, min: 40, max: 100 },
  series: modes.map((m) => ({
    name: MODE_LABELS[m],
    type: 'line' as const,
    data: learningEffectMastery[m],
    smooth: true,
    areaStyle: { color: COLORS[m], opacity: 0.15 },
    lineStyle: { color: COLORS[m], width: 2 },
    itemStyle: { color: COLORS[m] },
  })),
}

// 饼图 option 工厂函数
function makeGradePieOption(mode: keyof typeof COLORS) {
  const d = learningEffectGrades[mode]
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    color: gradeColors,
    series: [
      {
        type: 'pie' as const,
        radius: ['40%', '70%'],
        center: ['50%', '55%'],
        avoidLabelOverlap: true,
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        data: [
          { name: '优秀(A)', value: d.A },
          { name: '良好(B)', value: d.B },
          { name: '及格(C)', value: d.C },
          { name: '不及格(D)', value: d.D },
        ],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'center',
          style: { text: d.avg, fontSize: 18, fontWeight: 'bold', fill: '#374151' },
        },
      },
    ],
  }
}

export default function LearningEffectTab() {
  return (
    <ChartGrid>
      <div className="chart-card">
        <div className="chart-title">各检查点正确率对比</div>
        <ReactEChartsCore echarts={echarts} option={accuracyOption} style={{ height: 300 }} />
      </div>
      <div className="chart-card">
        <div className="chart-title">作业评级分布</div>
        <PieRow>
          {modes.map((m) => (
            <div key={m}>
              <div className="pie-label" style={{ color: COLORS[m] }}>
                {MODE_LABELS[m]}
              </div>
              <ReactEChartsCore
                echarts={echarts}
                option={makeGradePieOption(m)}
                style={{ height: 200 }}
              />
            </div>
          ))}
        </PieRow>
      </div>
      <div className="chart-card-full">
        <div className="chart-title">知识掌握度变化趋势</div>
        <ReactEChartsCore echarts={echarts} option={masteryOption} style={{ height: 300 }} />
      </div>
    </ChartGrid>
  )
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

---

### Task 5: 创建学生参与度 Tab 组件

**Files:**
- Create: `frontend/src/components/analytics/ParticipationTab.tsx`

- [ ] **Step 1: 创建 ParticipationTab.tsx**

```tsx
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import styled from 'styled-components'
import {
  COLORS,
  MODE_LABELS,
  participationQA,
  participationType,
  participationTrend,
} from './mockData'

echarts.use([
  BarChart, LineChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent,
  CanvasRenderer,
])

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  .chart-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }

  .chart-card-full {
    grid-column: 1 / -1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }
`

const PieRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-top: 4px;

  .pie-label {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
  }
`

const modes = Object.keys(COLORS) as (keyof typeof COLORS)[]
const typeColors = ['#22C55E', '#3B82F6', '#9CA3AF']

// 柱状图：提问次数 & 回答次数
const qaOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: ['提问次数', '回答次数'] },
  xAxis: { type: 'category' as const, data: participationQA.modes },
  yAxis: { type: 'value' as const },
  series: [
    {
      name: '提问次数',
      type: 'bar' as const,
      data: participationQA.questions,
      itemStyle: { color: '#3B82F6', borderRadius: [4, 4, 0, 0] },
    },
    {
      name: '回答次数',
      type: 'bar' as const,
      data: participationQA.answers,
      itemStyle: { color: '#A855F7', borderRadius: [4, 4, 0, 0] },
    },
  ],
}

// 折线图：各检查点参与度变化
const trendOption = {
  tooltip: { trigger: 'axis' },
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  xAxis: { type: 'category' as const, data: participationTrend.checkpoints },
  yAxis: { type: 'value' as const, min: 30, max: 100 },
  series: modes.map((m) => ({
    name: MODE_LABELS[m],
    type: 'line' as const,
    data: participationTrend[m],
    smooth: true,
    lineStyle: { color: COLORS[m], width: 2 },
    itemStyle: { color: COLORS[m] },
  })),
}

// 饼图 option 工厂函数
function makeTypePieOption(mode: keyof typeof COLORS) {
  const d = participationType[mode]
  const activePercent = d.active + d.passive
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    color: typeColors,
    series: [
      {
        type: 'pie' as const,
        radius: ['40%', '70%'],
        center: ['50%', '55%'],
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        data: [
          { name: '积极发言', value: d.active },
          { name: '被动回答', value: d.passive },
          { name: '旁听学习', value: d.bystander },
        ],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'center',
          style: {
            text: `${activePercent}%`,
            fontSize: 18,
            fontWeight: 'bold',
            fill: '#374151',
          },
        },
      },
    ],
  }
}

export default function ParticipationTab() {
  return (
    <ChartGrid>
      <div className="chart-card">
        <div className="chart-title">主动提问次数 & 回答次数</div>
        <ReactEChartsCore echarts={echarts} option={qaOption} style={{ height: 300 }} />
      </div>
      <div className="chart-card">
        <div className="chart-title">学生参与类型分布</div>
        <PieRow>
          {modes.map((m) => (
            <div key={m}>
              <div className="pie-label" style={{ color: COLORS[m] }}>
                {MODE_LABELS[m]}
              </div>
              <ReactEChartsCore
                echarts={echarts}
                option={makeTypePieOption(m)}
                style={{ height: 200 }}
              />
            </div>
          ))}
        </PieRow>
      </div>
      <div className="chart-card-full">
        <div className="chart-title">各检查点参与度变化</div>
        <ReactEChartsCore echarts={echarts} option={trendOption} style={{ height: 300 }} />
      </div>
    </ChartGrid>
  )
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

---

### Task 6: 创建学生满意度 Tab 组件

**Files:**
- Create: `frontend/src/components/analytics/SatisfactionTab.tsx`

- [ ] **Step 1: 创建 SatisfactionTab.tsx**

```tsx
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, RadarChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  RadarComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import styled from 'styled-components'
import {
  COLORS,
  MODE_LABELS,
  satisfactionLevels,
  satisfactionRadar,
  satisfactionNPS,
} from './mockData'

echarts.use([
  BarChart, RadarChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent, RadarComponent,
  CanvasRenderer,
])

const ChartGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  .chart-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }

  .chart-card-full {
    grid-column: 1 / -1;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 16px;

    .chart-title {
      font-size: 14px;
      font-weight: 600;
      color: #374151;
      margin-bottom: 12px;
    }
  }
`

const PieRow = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  margin-top: 4px;

  .pie-label {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
  }
`

const modes = Object.keys(COLORS) as (keyof typeof COLORS)[]
const levelColors = ['#22C55E', '#3B82F6', '#F59E0B', '#EF4444']

// 饼图：满意度等级分布
function makeLevelPieOption(mode: keyof typeof COLORS) {
  const d = satisfactionLevels[mode]
  const avgScore = Math.round(
    (d.verySatisfied * 95 + d.satisfied * 75 + d.neutral * 50 + d.dissatisfied * 20) / 100
  )
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}% ({d}%)' },
    color: levelColors,
    series: [
      {
        type: 'pie' as const,
        radius: ['40%', '70%'],
        center: ['50%', '55%'],
        label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
        data: [
          { name: '非常满意', value: d.verySatisfied },
          { name: '满意', value: d.satisfied },
          { name: '一般', value: d.neutral },
          { name: '不满意', value: d.dissatisfied },
        ],
        graphic: {
          type: 'text',
          left: 'center',
          top: 'center',
          style: {
            text: `${avgScore}`,
            fontSize: 18,
            fontWeight: 'bold',
            fill: '#374151',
          },
        },
      },
    ],
  }
}

// 雷达图：满意度细分维度
const radarOption = {
  tooltip: {},
  legend: { data: modes.map((m) => MODE_LABELS[m]) },
  radar: {
    indicator: satisfactionRadar.indicators.map((name) => ({ name, max: 100 })),
  },
  series: [
    {
      type: 'radar' as const,
      data: modes.map((m) => ({
        name: MODE_LABELS[m],
        value: satisfactionRadar[m],
        lineStyle: { color: COLORS[m] },
        itemStyle: { color: COLORS[m] },
        areaStyle: { color: COLORS[m], opacity: 0.1 },
      })),
    },
  ],
}

// 柱状图：NPS 净推荐值
const npsOption = {
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category' as const, data: satisfactionNPS.modes },
  yAxis: {
    type: 'value' as const,
    min: -100,
    max: 100,
    axisLabel: { formatter: '{value}' },
  },
  series: [
    {
      type: 'bar' as const,
      data: modes.map((m) => ({
        value: satisfactionNPS.scores[modes.indexOf(m) as 0 | 1 | 2],
        itemStyle: {
          color: COLORS[m],
          borderRadius: [4, 4, 0, 0],
        },
      })),
      barWidth: '40%',
    },
  ],
}

export default function SatisfactionTab() {
  return (
    <ChartGrid>
      <div className="chart-card">
        <div className="chart-title">满意度等级分布</div>
        <PieRow>
          {modes.map((m) => (
            <div key={m}>
              <div className="pie-label" style={{ color: COLORS[m] }}>
                {MODE_LABELS[m]}
              </div>
              <ReactEChartsCore
                echarts={echarts}
                option={makeLevelPieOption(m)}
                style={{ height: 200 }}
              />
            </div>
          ))}
        </PieRow>
      </div>
      <div className="chart-card">
        <div className="chart-title">满意度细分维度</div>
        <ReactEChartsCore echarts={echarts} option={radarOption} style={{ height: 300 }} />
      </div>
      <div className="chart-card-full">
        <div className="chart-title">NPS 净推荐值对比</div>
        <ReactEChartsCore echarts={echarts} option={npsOption} style={{ height: 300 }} />
      </div>
    </ChartGrid>
  )
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

---

### Task 7: 创建主页面并注册路由

**Files:**
- Create: `frontend/src/views/AnalyticsDashboard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 AnalyticsDashboard.tsx**

```tsx
import { useState } from 'react'
import styled from 'styled-components'
import { COLORS, MODE_LABELS, overviewScores } from '../components/analytics/mockData'
import OverviewTab from '../components/analytics/OverviewTab'
import LearningEffectTab from '../components/analytics/LearningEffectTab'
import ParticipationTab from '../components/analytics/ParticipationTab'
import SatisfactionTab from '../components/analytics/SatisfactionTab'

const tabs = [
  { key: 'overview', label: '总览' },
  { key: 'learning', label: '学习成效' },
  { key: 'participation', label: '学生参与度' },
  { key: 'satisfaction', label: '学生满意度' },
] as const

type TabKey = (typeof tabs)[number]['key']

const modes = Object.keys(COLORS) as (keyof typeof COLORS)[]

export default function AnalyticsDashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>('overview')

  return (
    <Wrapper>
      <div className="page-header">
        <h1 className="page-title">教学智能体效果分析</h1>
        <p className="page-subtitle">三种教学模式的教学效果对比（模拟数据，30名学生）</p>
      </div>

      {/* 指标卡片 */}
      <div className="score-cards">
        {modes.map((m) => (
          <div className="score-card" key={m} style={{ borderTopColor: COLORS[m] }}>
            <div className="score-label">{MODE_LABELS[m]} 综合评分</div>
            <div className="score-value" style={{ color: COLORS[m] }}>
              {overviewScores[m].overall}
            </div>
            <div className="score-max">/ 100</div>
          </div>
        ))}
      </div>

      {/* Tab 切换 */}
      <div className="tab-bar">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* 图表内容 */}
      <div className="tab-content">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'learning' && <LearningEffectTab />}
        {activeTab === 'participation' && <ParticipationTab />}
        {activeTab === 'satisfaction' && <SatisfactionTab />}
      </div>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #f3f4f6;
  padding: 32px 24px;
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;

  .page-header {
    text-align: center;
    margin-bottom: 32px;
  }

  .page-title {
    font-size: 28px;
    font-weight: 700;
    color: #111827;
    margin: 0 0 8px;
  }

  .page-subtitle {
    font-size: 14px;
    color: #6b7280;
    margin: 0;
  }

  .score-cards {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    max-width: 960px;
    margin: 0 auto 24px;
  }

  .score-card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border-top: 3px solid;
  }

  .score-label {
    font-size: 12px;
    color: #6b7280;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .score-value {
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
  }

  .score-max {
    font-size: 12px;
    color: #9ca3af;
    margin-top: 4px;
  }

  .tab-bar {
    display: flex;
    gap: 0;
    max-width: 960px;
    margin: 0 auto 24px;
    background: #fff;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    overflow: hidden;
  }

  .tab-button {
    flex: 1;
    padding: 12px 16px;
    border: none;
    background: transparent;
    font-size: 14px;
    font-weight: 500;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background: #f9fafb;
    }

    &.active {
      background: #3b82f6;
      color: #fff;
      font-weight: 600;
    }
  }

  .tab-content {
    max-width: 960px;
    margin: 0 auto;
  }

  @media (max-width: 768px) {
    padding: 16px 12px;

    .score-cards {
      grid-template-columns: 1fr;
      gap: 12px;
    }

    .tab-bar {
      flex-wrap: wrap;
    }

    .tab-button {
      flex: none;
      width: 50%;
    }

    .page-title {
      font-size: 22px;
    }
  }
`
```

- [ ] **Step 2: 注册路由**

修改 `frontend/src/App.tsx`，新增 import 和 Route：

```tsx
import AnalyticsDashboard from './views/AnalyticsDashboard'

// 在 <Routes> 中，`*` 通配路由之前添加：
<Route path="/analytics" element={<AnalyticsDashboard />} />
```

- [ ] **Step 3: 验证 TypeScript 编译**

```bash
cd frontend
npx tsc --noEmit --project tsconfig.app.json
```

Expected: 无错误。

- [ ] **Step 4: 验证开发服务器正常运行**

```bash
cd frontend
npm run dev
```

Expected: 打开 `http://localhost:5173/analytics` 能看到页面。

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/analytics/ frontend/src/views/AnalyticsDashboard.tsx frontend/src/App.tsx frontend/package.json frontend/package-lock.json
git commit -m "feat(analytics): 新增教学效果分析答辩页面

- 新增 /analytics 路由，Tab 切换展示四种分析维度
- 总览 Tab：指标卡片 + 柱状图 + 雷达图 + 折线图
- 学习成效 Tab：正确率柱状图 + 作业评级饼图 + 掌握度折线图
- 学生参与度 Tab：提问回答柱状图 + 参与类型饼图 + 活跃度折线图
- 学生满意度 Tab：等级分布饼图 + 细分雷达图 + NPS 柱状图
- 使用 ECharts + echarts-for-react，静态 mock 数据"
```

---

### Task 8: 最终验证

- [ ] **Step 1: 运行 lint**

```bash
cd frontend
npm run lint
```

Expected: 无错误或仅有已知的 warning。

- [ ] **Step 2: 运行构建**

```bash
cd frontend
npm run build
```

Expected: 构建成功，无 TypeScript 错误。

- [ ] **Step 3: 浏览器验证所有 Tab**

打开 `http://localhost:5173/analytics`，逐一点击四个 Tab，确认：
- 总览：3 个指标卡片 + 3 个图表正常渲染
- 学习成效：3 个图表（含 3 个饼图并排）正常渲染
- 学生参与度：3 个图表（含 3 个饼图并排）正常渲染
- 学生满意度：3 个图表（含 3 个饼图并排）正常渲染
- 响应式：缩小浏览器窗口，卡片和 Tab 自动适配

如发现视觉问题，调整 styled-components 中的样式后重新验证。
