// frontend/src/components/StudentChip.tsx
import styled from 'styled-components'
import type { StudentLevel } from '../types/observation'

interface StudentChipProps {
  /** 学生姓名 */
  name: string
  /** 学生水平 */
  level: StudentLevel
  /** 删除回调，不传则不显示删除按钮 */
  onDelete?: () => void
}

const LEVEL_LABELS: Record<StudentLevel, string> = {
  excellent: '优秀',
  average: '中等',
  basic: '基础',
}

const LEVEL_COLORS: Record<StudentLevel, { bg: string; color: string }> = {
  excellent: { bg: '#E3F2FD', color: '#1565C0' },
  average: { bg: '#FFF9C4', color: '#F57F17' },
  basic: { bg: '#FFECB3', color: '#E65100' },
}

export default function StudentChip({ name, level, onDelete }: StudentChipProps) {
  const levelColor = LEVEL_COLORS[level]

  return (
    <Wrapper>
      <span className="student-name">{name}</span>
      <span className="student-level" style={{ background: levelColor.bg, color: levelColor.color }}>
        {LEVEL_LABELS[level]}
      </span>
      {onDelete && (
        <button className="delete-btn" onClick={onDelete} aria-label={`删除 ${name}`}>
          ×
        </button>
      )}
    </Wrapper>
  )
}

const Wrapper = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #ffffff;
  border: 2px solid #1a1a1a;
  border-radius: 8px;
  box-shadow: 2px 2px 0px 0px #1a1a1a;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px 0px #1a1a1a;
  }

  .student-name {
    font-weight: 700;
    font-size: 14px;
    color: #1a1c1c;
  }

  .student-level {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
    border: 1px solid rgba(0, 0, 0, 0.1);
  }

  .delete-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: #e63946;
    font-size: 16px;
    padding: 0 2px;
    line-height: 1;

    &:hover {
      transform: scale(1.2);
    }
  }
`
