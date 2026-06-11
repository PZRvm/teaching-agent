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
