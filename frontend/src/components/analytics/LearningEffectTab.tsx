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
const gradeColors = ['#22C55E', '#3B82F6', '#F59E0B', '#EF4444']

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
