// frontend/src/views/ObservationConfig.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import StudentChip from '../components/StudentChip'
import RoughButton from '../components/RoughButton'
import Footer from '../components/Footer'
import { startObservation } from '../apis/observation'
import type { StudentProfile, TeachingMode } from '../types/observation'

export default function ObservationConfig() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [teachingMode, setTeachingMode] = useState<TeachingMode>('heuristic')
  const [students, setStudents] = useState<StudentProfile[]>([])
  const [studentName, setStudentName] = useState('')
  const [error, setError] = useState('')

  const handleAddStudent = () => {
    if (!studentName.trim()) return

    const newStudent: StudentProfile = {
      name: studentName.trim(),
      level: 'average',
      attitude: 'neutral',
      learning_ability: 5,
    }

    setStudents((prev) => [...prev, newStudent])
    setStudentName('')
    setError('')
  }

  const handleRemoveStudent = (index: number) => {
    setStudents((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    setError('')

    if (!topic.trim()) {
      setError('请输入教学主题')
      return
    }

    if (students.length === 0) {
      setError('请至少添加一名学生')
      return
    }

    try {
      const response = await startObservation({
        topic: topic.trim(),
        teaching_mode: teachingMode,
        checkpoint_count: 5,
        students,
      })
      navigate(`/observation/session/${response.session_id}`)
    } catch {
      setError('启动观察模式失败，请稍后重试')
    }
  }

  return (
    <Wrapper>
      <PageNav title="观察模式 - 配置" onBack={() => navigate('/')} />

      <main className="config-main">
        {error && <div className="error-banner">{error}</div>}

        {/* 步骤 1：教学主题 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">1</span>
            <h2 className="step-title">教学主题</h2>
          </div>
          <input
            type="text"
            className="topic-input"
            placeholder="例如：Python变量与数据类型"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </section>

        {/* 步骤 2：教学模式 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">2</span>
            <h2 className="step-title">教学模式</h2>
          </div>
          <div className="mode-buttons">
            <RoughButton
              variant={teachingMode === 'didactic' ? 'primary' : 'outline'}
              className={`mode-button ${teachingMode === 'didactic' ? 'selected' : ''}`}
              onClick={() => setTeachingMode('didactic')}
            >
              灌输式
            </RoughButton>
            <RoughButton
              variant={teachingMode === 'heuristic' ? 'primary' : 'outline'}
              className={`mode-button ${teachingMode === 'heuristic' ? 'selected' : ''}`}
              onClick={() => setTeachingMode('heuristic')}
            >
              启发式
            </RoughButton>
            <RoughButton
              variant={teachingMode === 'discussion' ? 'primary' : 'outline'}
              className={`mode-button ${teachingMode === 'discussion' ? 'selected' : ''}`}
              onClick={() => setTeachingMode('discussion')}
            >
              讨论式
            </RoughButton>
          </div>
        </section>

        {/* 步骤 3：学生配置 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">3</span>
            <h2 className="step-title">学生配置</h2>
          </div>
          <div className="student-add-row">
            <input
              type="text"
              className="student-name-input"
              placeholder="学生姓名"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddStudent()}
            />
            <RoughButton variant="secondary" onClick={handleAddStudent}>
              + 添加学生
            </RoughButton>
          </div>
          {students.length > 0 && (
            <div className="student-list">
              {students.map((student, index) => (
                <StudentChip
                  key={student.name}
                  name={student.name}
                  level={student.level}
                  onDelete={() => handleRemoveStudent(index)}
                />
              ))}
            </div>
          )}
        </section>

        {/* 开始按钮 */}
        <div className="action-row">
          <RoughButton variant="primary" className="submit-button" onClick={handleSubmit}>
            开始观察
          </RoughButton>
        </div>
      </main>

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #fafafa;
  color: #1a1a1a;
  font-family: 'Be Vietnam Pro', system-ui, sans-serif;

  .error-banner {
    background: #fce4ec;
    border: 2px solid #e63946;
    border-radius: 8px;
    box-shadow: 3px 3px 0px 0px #e63946;
    padding: 12px 16px;
    font-weight: 600;
    color: #e63946;
    text-align: center;
  }

  .config-main {
    max-width: 800px;
    margin: 0 auto;
    padding: 32px 24px 80px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .step-card {
    background: #fff9c4;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 24px;
    transform: rotate(-0.3deg);
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .step-number {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #2e5cff;
    color: #fff;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .step-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 20px;
    font-weight: 700;
    margin: 0;
  }

  .topic-input {
    width: 100%;
    padding: 12px 16px;
    font-size: 16px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 2px 2px 0px 0px #1a1a1a;

    &:focus {
      outline: none;
      box-shadow: 2px 2px 0px 0px #2e5cff;
    }

    &::placeholder {
      color: #6c757d;
    }
  }

  .mode-buttons {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .mode-button {
    flex: 1;
    min-width: 100px;
  }

  .student-add-row {
    display: flex;
    gap: 12px;

    > *:first-child {
      flex: 1;
    }
  }

  .student-name-input {
    padding: 10px 14px;
    font-size: 14px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    background: #ffffff;
    box-shadow: 2px 2px 0px 0px #1a1a1a;

    &:focus {
      outline: none;
      box-shadow: 2px 2px 0px 0px #2e5cff;
    }
  }

  .student-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
  }

  .action-row {
    display: flex;
    justify-content: center;
    margin-top: 16px;
  }

  .submit-button {
    min-width: 200px;
    padding: 14px 32px;
    font-size: 18px;
    font-weight: 700;
  }
`
