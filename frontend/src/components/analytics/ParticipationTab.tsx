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
