// frontend/src/views/ObservationConfig.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import StudentChip from '../components/StudentChip'
import RoughButton from '../components/RoughButton'
import Footer from '../components/Footer'
import Loading from '../components/Loading'
import { startObservation } from '../apis/observation'
import type { StudentProfile, TeachingMode, StudentLevel, StudentAttitude, StudentCreateSource } from '../types/observation'
import { STUDENT_LEVEL_OPTIONS, STUDENT_ATTITUDE_OPTIONS } from '../types/observation'

interface ManualStudentInput {
  name: string
  gender: string
  level: StudentLevel
  attitude: StudentAttitude
  learning_ability: number
  background: string
  special_traits: string
}

export default function ObservationConfig() {
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [teachingMode, setTeachingMode] = useState<TeachingMode>('heuristic')
  const [checkpointCount, setCheckpointCount] = useState(5)
  const [students, setStudents] = useState<StudentProfile[]>([])

  // 加载状态
  const [isLoading, setIsLoading] = useState(false)

  // 学生创建方式
  const [studentSource, setStudentSource] = useState<StudentCreateSource>('manual')

  // 手动输入表单
  const [manualInput, setManualInput] = useState<ManualStudentInput>({
    name: '',
    gender: '',
    level: 'average',
    attitude: 'neutral',
    learning_ability: 5,
    background: '',
    special_traits: '',
  })

  // 随机生成配置
  const [randomConfig, setRandomConfig] = useState({
    total_students: 10,
    level_distribution_excellent: 30,
    level_distribution_average: 50,
    level_distribution_basic: 20,
    attitude_distribution_active: 30,
    attitude_distribution_neutral: 50,
    attitude_distribution_passive: 20,
    random_seed: '',
  })

  // JSON 数据
  const [jsonData, setJsonData] = useState('')
  const [jsonError, setJsonError] = useState('')

  const [error, setError] = useState('')
  const [showManualForm, setShowManualForm] = useState(false)

  const handleAddManualStudent = () => {
    if (!manualInput.name.trim()) {
      setError('请输入学生姓名')
      return
    }

    const newStudent: StudentProfile = {
      name: manualInput.name.trim(),
      gender: manualInput.gender || null,
      level: manualInput.level,
      attitude: manualInput.attitude,
      learning_ability: manualInput.learning_ability,
      background: manualInput.background || null,
      special_traits: manualInput.special_traits
        ? manualInput.special_traits.split(',').map(s => s.trim()).filter(Boolean)
        : [],
    }

    setStudents((prev) => [...prev, newStudent])
    setManualInput({
      name: '',
      gender: '',
      level: 'average',
      attitude: 'neutral',
      learning_ability: 5,
      background: '',
      special_traits: '',
    })
    setShowManualForm(false)
    setError('')
  }

  const handleRemoveStudent = (index: number) => {
    setStudents((prev) => prev.filter((_, i) => i !== index))
  }

  const handleGenerateRandom = () => {
    const total = randomConfig.total_students
    const generated: StudentProfile[] = []

    // 简化版随机生成（前端预览用）
    const namePool = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十', '郑十一', '王十二', '冯十三', '陈十四', '褚十五', '卫十六', '蒋十七', '沈十八', '韩十九', '杨二十', '朱二十一', '秦二十二', '尤二十三', '许二十四', '何二十五', '吕二十六', '施二十七', '张二十八', '孔二十九', '曹三十', '卫三十', '蒋三一', '沈三二', '韩三三', '杨三四', '朱三五', '秦三六', '尤三七', '许三八', '何三九', '吕四十', '施四一', '张四二', '孔四三', '曹四四', '卫四五', '蒋四六', '沈四七', '韩四八', '杨四九', '朱五十']

    const learningAbilityRanges: Record<StudentLevel, [number, number]> = {
      excellent: [7, 10],
      average: [4, 7],
      basic: [1, 4],
    }

    // 获取已使用的姓名
    const usedNames = new Set(students.map(s => s.name))

    // 生成学生池
    const levelPool: StudentLevel[] = []
    const excellentCount = Math.floor(total * randomConfig.level_distribution_excellent / 100)
    const averageCount = Math.floor(total * randomConfig.level_distribution_average / 100)
    const basicCount = total - excellentCount - averageCount // 确保总数正确

    for (let i = 0; i < excellentCount; i++) levelPool.push('excellent')
    for (let i = 0; i < averageCount; i++) levelPool.push('average')
    for (let i = 0; i < basicCount; i++) levelPool.push('basic')

    const attitudePool: StudentAttitude[] = []
    const activeCount = Math.floor(total * randomConfig.attitude_distribution_active / 100)
    const neutralCount = Math.floor(total * randomConfig.attitude_distribution_neutral / 100)
    const passiveCount = total - activeCount - neutralCount // 确保总数正确

    for (let i = 0; i < activeCount; i++) attitudePool.push('active')
    for (let i = 0; i < neutralCount; i++) attitudePool.push('neutral')
    for (let i = 0; i < passiveCount; i++) attitudePool.push('passive')

    // 洗牌算法
    const shuffle = <T,>(array: T[]): T[] => {
      const result = [...array]
      for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[result[i], result[j]] = [result[j], result[i]]
      }
      return result
    }

    const shuffledLevels = shuffle(levelPool)
    const shuffledAttitudes = shuffle(attitudePool)

    let generatedCount = 0
    let nameIndex = 0

    while (generatedCount < total && nameIndex < namePool.length) {
      const name = namePool[nameIndex]
      nameIndex++

      // 跳过已使用的姓名
      if (usedNames.has(name)) {
        continue
      }

      const level = shuffledLevels[generatedCount % shuffledLevels.length] || 'average'
      const attitude = shuffledAttitudes[generatedCount % shuffledAttitudes.length] || 'neutral'
      const [laMin, laMax] = learningAbilityRanges[level]
      const learningAbility = Math.floor(Math.random() * (laMax - laMin + 1)) + laMin

      generated.push({
        name,
        gender: Math.random() > 0.5 ? '男' : '女',
        level,
        attitude,
        learning_ability: learningAbility,
        background: null,
        special_traits: [],
      })

      generatedCount++
    }

    // 叠加到现有学生列表
    setStudents((prev) => [...prev, ...generated])
    setError('')
    // 切换到手动输入标签页以显示生成的学生
    setStudentSource('manual')
  }

  const handleImportJson = () => {
    setJsonError('')
    try {
      const data = JSON.parse(jsonData)
      if (!Array.isArray(data)) {
        throw new Error('JSON 数据应该是学生列表')
      }
      if (data.length < 2) {
        throw new Error('至少需要2个学生')
      }

      const imported: StudentProfile[] = data.map(item => ({
        name: item.name || '',
        gender: item.gender || null,
        level: item.level || 'average',
        attitude: item.attitude || 'neutral',
        learning_ability: item.learning_ability || 5,
        background: item.background || null,
        special_traits: item.special_traits || [],
      }))

      setStudents((prev) => [...prev, ...imported])
      setJsonData('')
      // 切换到手动输入标签页以显示导入的学生
      setStudentSource('manual')
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'JSON 格式错误')
    }
  }

  const handleSubmit = async () => {
    setError('')

    if (!topic.trim()) {
      setError('请输入教学主题')
      return
    }

    if (students.length < 2) {
      setError('请至少添加2名学生')
      return
    }

    setIsLoading(true)
    try {
      console.log('提交观察模式配置:', { topic, teachingMode, students })
      const response = await startObservation({
        topic: topic.trim(),
        teaching_mode: teachingMode,
        checkpoint_count: checkpointCount,
        students,
      })
      console.log('后端返回响应:', response)
      console.log('准备跳转到:', `/observation/session/${response.session_id}`)
      navigate(`/observation/session/${response.session_id}`)
    } catch (err) {
      console.error('启动观察模式失败:', err)
      setError('启动观察模式失败，请稍后重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Wrapper>
      <PageNav title="观察模式 - 配置" onBack={() => navigate('/')} />

      <main className="config-main">
        {/* Hero Section */}
        <header className="hero">
          <h1 className="hero-title">
            观察模式
            <svg className="hero-underline" viewBox="0 0 100 20" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 10 Q 25 0, 50 10 T 100 10" fill="transparent" stroke="currentColor" strokeLinecap="round" strokeWidth="4" />
            </svg>
          </h1>
          <p className="hero-subtitle">
            旁观 AI 教学与多 Agent 互动
            <svg className="hero-subtitle-line" viewBox="0 0 100 10" preserveAspectRatio="none" aria-hidden="true">
              <path d="M0 5 L 100 5" fill="transparent" stroke="currentColor" strokeDasharray="5 5" strokeWidth="2" />
            </svg>
          </p>
        </header>

        {error && <div className="error-banner">{error}</div>}

        {/* 步骤 1：教学主题 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">1</span>
            <h2 className="step-title">教学主题</h2>
          </div>
          <input type="text" className="topic-input" placeholder="例如：Python变量与数据类型" value={topic} onChange={(e) => setTopic(e.target.value)} />
        </section>

        {/* 步骤 2：教学模式 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">2</span>
            <h2 className="step-title">教学模式</h2>
          </div>
          <div className="mode-buttons">
            <RoughButton variant={teachingMode === 'didactic' ? 'primary' : 'outline'} className={`mode-button ${teachingMode === 'didactic' ? 'selected' : ''}`} onClick={() => setTeachingMode('didactic')}>
              灌输式
            </RoughButton>
            <RoughButton variant={teachingMode === 'heuristic' ? 'primary' : 'outline'} className={`mode-button ${teachingMode === 'heuristic' ? 'selected' : ''}`} onClick={() => setTeachingMode('heuristic')}>
              启发式
            </RoughButton>
            <RoughButton variant={teachingMode === 'discussion' ? 'primary' : 'outline'} className={`mode-button ${teachingMode === 'discussion' ? 'selected' : ''}`} onClick={() => setTeachingMode('discussion')}>
              讨论式
            </RoughButton>
          </div>
        </section>

        {/* 步骤 2.5：检查点数量 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">2.5</span>
            <h2 className="step-title">检查点数量</h2>
          </div>
          <input type="number" className="topic-input" min="1" max="10" value={checkpointCount} onChange={(e) => setCheckpointCount(Math.max(1, Math.min(10, Number(e.target.value))))} />
          <p className="checkpoint-hint">建议 3-7 个，每个检查点涵盖一个知识点</p>
        </section>

        {/* 步骤 3：学生配置 */}
        <section className="step-card">
          <div className="step-header">
            <span className="step-number">3</span>
            <h2 className="step-title">学生配置</h2>
          </div>

          {/* 创建方式选择 */}
          <div className="source-tabs">
            <button className={`source-tab ${studentSource === 'manual' ? 'active' : ''}`} onClick={() => setStudentSource('manual')}>
              手动输入
            </button>
            <button className={`source-tab ${studentSource === 'random' ? 'active' : ''}`} onClick={() => setStudentSource('random')}>
              随机生成
            </button>
            <button className={`source-tab ${studentSource === 'json' ? 'active' : ''}`} onClick={() => setStudentSource('json')}>
              JSON 导入
            </button>
          </div>

          {studentSource === 'manual' && (
            <div className="manual-section">
              <div className="student-list">
                {students.map((student, index) => (
                  <StudentChip key={student.name} name={student.name} level={student.level} onDelete={() => handleRemoveStudent(index)} />
                ))}
              </div>

              <button className="add-student-btn" onClick={() => setShowManualForm(true)}>
                + 添加学生
              </button>

              {showManualForm && (
                <div className="manual-form">
                  <h3>添加学生</h3>

                  <div className="form-row">
                    <label htmlFor="student-name">姓名 *</label>
                    <input id="student-name" type="text" className="form-input" value={manualInput.name} onChange={(e) => setManualInput({ ...manualInput, name: e.target.value })} />
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-level">水平</label>
                    <select id="student-level" className="form-select" value={manualInput.level} onChange={(e) => setManualInput({ ...manualInput, level: e.target.value as StudentLevel })}>
                      {STUDENT_LEVEL_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-attitude">态度</label>
                    <select id="student-attitude" className="form-select" value={manualInput.attitude} onChange={(e) => setManualInput({ ...manualInput, attitude: e.target.value as StudentAttitude })}>
                      {STUDENT_ATTITUDE_OPTIONS.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-learning-ability">学习能力 (1-10)</label>
                    <input id="student-learning-ability" type="number" min="1" max="10" className="form-input" value={manualInput.learning_ability} onChange={(e) => setManualInput({ ...manualInput, learning_ability: Number(e.target.value) })} />
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-gender">性别</label>
                    <select id="student-gender" className="form-select" value={manualInput.gender} onChange={(e) => setManualInput({ ...manualInput, gender: e.target.value })}>
                      <option value="">不指定</option>
                      <option value="男">男</option>
                      <option value="女">女</option>
                    </select>
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-background">背景</label>
                    <input id="student-background" type="text" className="form-input" placeholder="可选" value={manualInput.background} onChange={(e) => setManualInput({ ...manualInput, background: e.target.value })} />
                  </div>

                  <div className="form-row">
                    <label htmlFor="student-special-traits">特殊特质</label>
                    <input id="student-special-traits" type="text" className="form-input" placeholder="逗号分隔，可选" value={manualInput.special_traits} onChange={(e) => setManualInput({ ...manualInput, special_traits: e.target.value })} />
                  </div>

                  <div className="form-actions">
                    <RoughButton variant="primary" onClick={handleAddManualStudent}>确认添加</RoughButton>
                    <RoughButton variant="outline" onClick={() => { setShowManualForm(false); setManualInput({ name: '', gender: '', level: 'average', attitude: 'neutral', learning_ability: 5, background: '', special_traits: '' }) }}>取消</RoughButton>
                  </div>
                </div>
              )}
            </div>
          )}

          {studentSource === 'random' && (
            <div className="random-section">
              <div className="form-row">
                <label htmlFor="random-total">学生数量 (2-50)</label>
                <input id="random-total" type="number" min="2" max="50" className="form-input" value={randomConfig.total_students} onChange={(e) => setRandomConfig({ ...randomConfig, total_students: Number(e.target.value) })} />
              </div>

              <div className="form-row">
                <label htmlFor="random-excellent">优秀比例 (%)</label>
                <input id="random-excellent" type="number" min="0" max="100" className="form-input" value={randomConfig.level_distribution_excellent} onChange={(e) => setRandomConfig({ ...randomConfig, level_distribution_excellent: Number(e.target.value) })} />
              </div>

              <div className="form-row">
                <label htmlFor="random-average">中等比例 (%)</label>
                <input id="random-average" type="number" min="0" max="100" className="form-input" value={randomConfig.level_distribution_average} onChange={(e) => setRandomConfig({ ...randomConfig, level_distribution_average: Number(e.target.value) })} />
              </div>

              <div className="form-row">
                <label htmlFor="random-basic">基础比例 (%)</label>
                <input id="random-basic" type="number" min="0" max="100" className="form-input" value={randomConfig.level_distribution_basic} onChange={(e) => setRandomConfig({ ...randomConfig, level_distribution_basic: Number(e.target.value) })} />
              </div>

              <div className="form-actions">
                <RoughButton variant="primary" onClick={handleGenerateRandom}>生成学生</RoughButton>
              </div>
            </div>
          )}

          {studentSource === 'json' && (
            <div className="json-section">
              <p className="json-hint">粘贴 JSON 格式的学生列表：</p>
              <textarea
                className="json-textarea"
                rows={10}
                placeholder='[{"name": "张三", "level": "excellent", "attitude": "active", "learning_ability": 8}]'
                value={jsonData}
                onChange={(e) => setJsonData(e.target.value)}
              />
              {jsonError && <div className="json-error">{jsonError}</div>}
              <RoughButton variant="primary" onClick={handleImportJson}>导入</RoughButton>
            </div>
          )}

          <div className="student-summary">
            已添加 <strong>{students.length}</strong> 名学生
          </div>
        </section>

        {/* 开始按钮 */}
        <div className="action-row">
          <RoughButton variant="primary" className="submit-button" onClick={handleSubmit} disabled={isLoading}>
            {isLoading ? '启动中...' : '开始观察'}
          </RoughButton>
        </div>
      </main>

      {/* 加载覆盖层 */}
      {isLoading && (
        <div className="loading-overlay">
          <Loading size="large" message="正在启动观察模式..." />
        </div>
      )}

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  background: #fafafa;

  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(250, 250, 250, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
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

  /* ===== Hero Section ===== */
  .hero {
    text-align: center;
    margin-bottom: 48px;
  }

  .hero-title {
    position: relative;
    display: inline-block;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 16px;
    color: #1a1c1c;
  }

  .hero-underline {
    position: absolute;
    bottom: -16px;
    left: 0;
    width: 100%;
    height: 16px;
    color: #2e5cff;
  }

  .hero-subtitle {
    position: relative;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    color: #525252;
    margin-top: 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .hero-subtitle-line {
    width: 192px;
    height: 8px;
    color: #b7102a;
    margin-top: 8px;
  }

  /* ===== 步骤卡片 ===== */
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

  .checkpoint-hint {
    font-size: 13px;
    color: #6c757d;
    margin: 8px 0 0 0;
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

  /* ===== 学生配置 ===== */
  .source-tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
  }

  .source-tab {
    padding: 8px 16px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    background: #ffffff;
    cursor: pointer;
    font-weight: 600;
    box-shadow: 2px 2px 0px 0px #1a1a1a;

    &:hover {
      transform: translate(-1px, -1px);
      box-shadow: 3px 3px 0px 0px #1a1a1a;
    }

    &.active {
      background: #2e5cff;
      color: #fff;
    }
  }

  .manual-section,
  .random-section,
  .json-section {
    margin-top: 16px;
  }

  .student-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
  }

  .add-student-btn {
    width: 100%;
    padding: 12px;
    border: 2px dashed #1a1a1a;
    border-radius: 8px;
    background: #ffffff;
    cursor: pointer;
    font-weight: 600;
    color: #6c757d;

    &:hover {
      background: #f5f5f5;
    }
  }

  .manual-form {
    margin-top: 20px;
    padding: 20px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    background: #fafafa;
    box-shadow: 2px 2px 0px 0px #1a1a1a;

    h3 {
      font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
      font-size: 18px;
      font-weight: 700;
      margin: 0 0 16px 0;
    }
  }

  .form-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 16px;

    label {
      font-weight: 600;
      font-size: 14px;
    }
  }

  .form-input,
  .form-select {
    padding: 10px 12px;
    font-size: 14px;
    border: 2px solid #1a1a1a;
    border-radius: 6px;
    background: #ffffff;

    &:focus {
      outline: none;
      box-shadow: 2px 2px 0px 0px #2e5cff;
    }
  }

  .form-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .student-summary {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #d4d4d4;
    font-size: 14px;
    color: #6c757d;
  }

  .json-hint {
    font-size: 14px;
    color: #6c757d;
    margin-bottom: 8px;
  }

  .json-textarea {
    width: 100%;
    padding: 12px;
    font-family: 'Courier New', monospace;
    font-size: 14px;
    border: 2px solid #1a1a1a;
    border-radius: 8px;
    resize: vertical;
    box-shadow: 2px 2px 0px 0px #1a1a1a;

    &:focus {
      outline: none;
      box-shadow: 2px 2px 0px 0px #2e5cff;
    }
  }

  .json-error {
    margin-top: 8px;
    padding: 8px 12px;
    background: #fce4ec;
    border: 2px solid #e63946;
    border-radius: 6px;
    font-size: 14px;
    color: #e63946;
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
