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
