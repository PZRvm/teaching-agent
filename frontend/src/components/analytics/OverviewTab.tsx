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
