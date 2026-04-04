# 开发路线图

项目：教学智能体  
分支：main  
开始日期：2026-04-04

## 开发顺序

### Phase 1: 基础设施与数据层

**目标**: 建立数据库基础设施和核心数据模型

**任务列表**:
1. 数据库ORM模型
   - [✓] `backend/orm/teaching_session.py` - TeachingSessionModel
   - [✓] `backend/orm/session_memory.py` - SessionMemoryModel
   - [✓] `backend/orm/teacher_memory.py` - TeacherMemoryModel
   - [✓] `backend/orm/message.py` - MessageModel

2. Alembic迁移脚本
   - [✓] 创建 `backend/alembic/versions/001_create_tables.py`
   - [✓] 定义所有表结构
   - [✓] 运行 `alembic upgrade head`

3. 基础Pydantic schemas
   - [✓] `backend/schemas/teaching_session.py` - TeachingSession
   - [✓] `backend/schemas/student.py` - StudentProfile, StudentCreateRequest
   - [✓] `backend/schemas/message.py` - Message, MessageType

**验收标准**:
- [✓] 数据库表创建成功（5张表：teaching_sessions, session_memories, teacher_memories, messages, alembic_version）
- [✓] 能通过代码创建TeachingSession并保存到数据库
- [✓] 能从数据库读取TeachingSession
- [✓] 验证：手动插入一条测试数据，读取确认

**预计时间**: 2-3小时

---

### Phase 2: 学生创建系统

**目标**: 实现三种学生创建方式（手动/随机/JSON）

**任务列表**:
1. StudentProfile schema + Field验证
   - [✓] name: `Field(min_length=1, max_length=20)`
   - [✓] learning_ability: `Field(ge=1, le=10)`
   - [✓] level, attitude枚举定义

2. NamePool服务
   - [✓] `backend/core/name_pool.py` - ~100个常用中文名字
   - [✓] 随机选择无重复

3. StudentFactory核心逻辑
   - [✓] `backend/core/student_factory.py`
   - [✓] `create_students(source="manual")` - 手动创建
   - [✓] `create_students(source="random")` - 随机生成
   - [✓] `create_students(source="json")` - JSON导入

4. RandomClassConfig + 随机生成逻辑
   - [✓] 按分布比例生成学生
   - [✓] 支持random_seed可复现

5. JSON导入/导出 + 验证
   - [✓] Pydantic schema验证
   - [✓] 导出功能

**验收标准**:
- [✓] 手动创建：能添加2-8个学生，验证生效
- [✓] 随机生成：输入班级人数30，分布"优秀30%/中等50%/基础20%"，实际分布符合
- [✓] JSON导入：能导入JSON文件，验证错误字段
- [ ] 验证：通过API手动测试三种创建方式（待 API 层实现）

**完成时间**: 2026-04-04

---

### Phase 3: Memory系统（核心）

**目标**: 实现agent记忆管理和数据库持久化

**任务列表**:
1. SessionMemory
   - [x] `backend/agents/memories/session_memory.py` - SessionMemory类
   - [x] message_history列表
   - [x] teaching_summary
   - [x] should_update_summary() 判断逻辑

2. TeacherAgentMemory
   - [x] `backend/agents/memories/teacher_memory.py` - TeacherAgentMemory类
   - [x] covered_topics追踪
   - [x] student_questions字典
   - [x] student_participation字典
   - [x] get_system_prompt_addition()

3. StudentAgentMemory
   - [x] `backend/agents/memories/student_memory.py` - StudentAgentMemory类
   - [x] learned_concepts - 已掌握概念列表
   - [x] current_knowledge_level - 当前知识水平（0-1）
   - [x] should_remember_concept() - 基于学习参数判断是否记住
   - [x] update_knowledge() - 尝试学习新概念
   - [x] get_system_prompt_addition() - 生成学生 prompt 上下文

4. MemoryManager
   - [x] `backend/agents/memories/memory_manager.py` - MemoryManager类
   - [x] process_message() 方法
   - [x] _process_lecture() - 提取知识点并更新学生记忆
   - [x] _check_and_update_summary() - LLM生成摘要
   - [x] register_student() - 注册学生到记忆系统

5. MemoryPersistence服务
   - [x] `backend/agents/memories/memory_persistence.py`
   - [x] _upsert() 通用方法
   - [x] save_session_memory()
   - [x] save_teacher_memory()
   - [x] save_student_memory()
   - [x] save_message()
   - [x] load_session_memory()
   - [x] load_teacher_memory()
   - [x] load_student_memory()
   - [x] _load_message_history()

**验收标准**:
- [x] 消息能添加到message_history
- [x] 每10条消息触发一次摘要更新（通过测试验证）
- [x] 会话结束后能从数据库完整恢复所有数据（SessionMemory + TeacherAgentMemory + StudentAgentMemory）
- [x] StudentAgentMemory 正常持久化和加载
- [x] 学生学习状态（learned_concepts, knowledge_level）正确保存和恢复
- [x] 并发更新不丢失数据（测试同时更新）
- [x] 验证：创建会话→添加消息→持久化→读取恢复

**完成时间**: 2026-04-04

---

### Phase 4: 教师Agent（单个，先做基础）

**目标**: 实现教师Agent的基础功能

**任务列表**:
1. LangChain基础集成
   - [ ] 配置硅基流动API（Qwen2.5-7B-Instruct）
   - [ ] 测试LLM连接

2. MemoryAwareTeacherAgent基础结构
   - [ ] `backend/agents/teacher_agent.py`
   - [ ] __init__ with MemoryManager and LLM
   - [ ] _create_agent() - LangChain AgentExecutor

3. 讲授功能
   - [ ] deliver_lecture() 方法
   - [ ] 根据teaching_mode调整讲授风格

**验收标准**:
- [ ] 能连接LLM API
- [ ] 能输出讲授内容（lecture）
- [ ] 讲授内容与教学主题相关
- [ ] 验证：调用agent，查看输出内容

**预计时间**: 2-3小时

---

### Phase 5: 学生Agent（单个）

**目标**: 实现学生Agent的基础功能

**任务列表**:
1. MemoryAwareStudentAgent基础结构
   - [ ] `backend/agents/student_agent.py`
   - [ ] __init__ with StudentAgentMemory and LLM

2. 回答功能
   - [ ] answer_question() 方法
   - [ ] 基于level参数差异化回答质量
   - [ ] 基于attitude参数差异化主动性

3. should_respond() 判断
   - [ ] 积极学生更主动响应
   - [ ] 消极学生响应较少

**验收标准**:
- [ ] 学生能回答问题
- [ ] level=优秀的学生比level=基础的学生回答质量更高
- [ ] attitude=积极的学生更主动（回答更多问题）
- [ ] 验证：创建两个不同level的学生，提问对比

**预计时间**: 2-3小时

---

### Phase 6: 三种教学模式实现

**目标**: 实现灌输式、启发式、讨论式三种教学模式的差异化

**任务列表**:
1. 灌输式模式
   - [ ] system prompt设计
   - [ ] 连续讲授逻辑
   - [ ] 无互动提问

2. 启发式模式
   - [ ] system prompt设计
   - [ ] 讲授3-5个知识点后提问
   - [ ] ask_checkpoint_question() 方法

3. 讨论式模式
   - [ ] system prompt设计
   - [ ] 频繁提问（每1-2个知识点）
   - [ ] ask_discussion_question() 方法

4. 作业和反馈
   - [ ] assign_homework()
   - [ ] grade_homework() - LLM评价
   - [ ] end_feedback()
   - [ ] collect_feedback()

**验收标准**:
- [ ] 灌输式：连续讲授，无提问
- [ ] 启发式：讲授后提问checkpoint问题
- [ ] 讨论式：频繁提问，引导学生讨论
- [ ] 三种模式的system prompt风格明显不同
- [ ] 验证：运行三种模式对比输出风格

**预计时间**: 4-5小时

---

### Phase 7: SessionOrchestrator（观察模式核心）

**目标**: 实现观察模式的自动教学流程编排

**任务列表**:
1. SessionOrchestrator基础结构
   - [ ] `backend/services/session_orchestrator.py`
   - [ ] __init__ with teacher_agent and student_agents

2. run_autonomous_session() 主循环
   - [ ] 循环直到教学内容完成
   - [ ] 根据teaching_mode调用不同方法

3. 三种模式的run_*_teaching方法
   - [ ] _run_didactic_teaching()
   - [ ] _run_heuristic_teaching()
   - [ ] _run_discussion_teaching()

4. 内容完成判断
   - [ ] _is_teaching_content_complete()
   - [ ] 教师Agent判断内容是否完成（可基于知识点覆盖率）

5. 作业和反馈流程
   - [ ] _assign_homework()
   - [ ] _collect_homework_and_feedback()

**验收标准**:
- [ ] 能自动运行完整教学流程
- [ ] 教学内容完成后自动结束（不依赖时长）
- [ ] 能布置作业和收集反馈
- [ ] 验证：创建观察会话，自动运行到结束

**预计时间**: 3-4小时

---

### Phase 8: WebSocket通信

**目标**: 实现前后端实时双向通信

**任务列表**:
1. WebSocket端点
   - [ ] `backend/routers/websocket.py`
   - [ ] /ws/{session_id} 端点
   - [ ] 连接管理（accept, close）

2. 消息广播机制
   - [ ] 连接池管理
   - [ ] send_json() 广播消息到所有连接

3. 心跳机制
   - [ ] ping/pong心跳
   - [ ] 断线处理

**验收标准**:
- [ ] 前端能建立WebSocket连接
- [ ] 后端能实时推送消息
- [ ] 多个客户端同时连接都能收到消息
- [ ] 连接断开时有处理
- [ ] 验证：前端连接，后端发送测试消息

**预计时间**: 2-3小时

---

### Phase 9: 后端API整合

**目标**: 实现所有REST API端点

**任务列表**:
1. 观察模式API
   - [ ] `backend/models/observation/router.py`
   - [ ] POST /observation/start
   - [ ] GET /observation/{session_id}/report

2. 学生创建API
   - [ ] `backend/models/student/router.py`
   - [ ] POST /students/create
   - [ ] POST /students/export
   - [ ] GET /students/templates

3. 会话管理API
   - [ ] `backend/models/session/router.py`
   - [ ] GET /sessions/{session_id}
   - [ ] GET /sessions/{session_id}/status

**验收标准**:
- [ ] POST /observation/start 能创建观察会话并返回session_id
- [ ] GET /observation/{id}/report 能生成完整报告
- [ ] POST /students/create 能创建学生（三种方式）
- [ ] 验证：使用curl或Postman测试所有API

**预计时间**: 2-3小时

---

### Phase 10: 观察模式前端（核心UI）

**目标**: 实现观察模式的完整UI流程

**任务列表**:
1. WebSocket hook
   - [ ] `frontend/src/hooks/useWebSocket.ts`
   - [ ] 连接管理
   - [ ] 消息接收
   - [ ] 断线重连

2. ObservationConfig组件
   - [ ] 教学主题输入
   - [ ] 教学模式选择（灌输式/启发式/讨论式）
   - [ ] 学生配置（StudentFactory三种模式切换UI）
   - [ ] "开始观察"按钮

3. ObservationView组件
   - [ ] 实时消息列表显示
   - [ ] 当前模式徽章显示
   - [� 已进行时间显示
   - [ ] 消息数量统计

**验收标准**:
- [ ] 能配置主题、模式、学生
- [ ] 能点击"开始观察"
- [ ] 能实时看到agent对话（WebSocket更新）
- [ ] 会话结束后自动跳转到报告页面
- [ ] 验证：完整体验一次观察模式流程

**预计时间**: 4-5小时

---

### Phase 11: 分析报告

**目标**: 实现量化分析报告生成和展示

**任务列表**:
1. ObservationAnalyzer服务
   - [ ] `backend/services/analyzer.py`
   - [ ] analyze_session() - 计算量化指标
   - [ ] 计算逻辑：
     - [ ] interaction_frequency（互动频率）
     - [ ] student_participation_rate（参与率）
     - [ ] average_knowledge_gain（知识掌握度提升）
     - [ ] average_correct_rate（平均正确率）

2. AnalysisReport组件
   - [ ] `frontend/src/components/AnalysisReport.tsx`
   - [ ] 课程和配置摘要显示
   - [ ] 量化指标卡片
   - [ ] 学生个体统计对比

**验收标准**:
- [ ] 显示5个以上量化指标
- [ ] 按学生分组显示统计
- [ ] 所有指标数值计算正确
- [ ] 验证：运行一次观察模式，检查报告数据

**预计时间**: 3-4小时

---

### Phase 12: 教师模式前端（辅助功能）

**目标**: 实现教师模式的UI（用于开发测试）

**任务列表**:
1. TeacherConfig组件
   - [ ] 配置界面（复用StudentFactory）
   - [ ] "开始教学"按钮

2. TeacherView组件
   - [ ] 用户输入区域
   - [ ] 学生响应显示
   - [ ] 消息列表（复用）

**验收标准**:
- [ ] 能配置并开始教师模式
- [ ] 能输入教学内容
- [ ] 能看到学生响应
- [ ] 能布置作业和查看反馈
- [ ] 验证：完整体验一次教师模式流程

**预计时间**: 2-3小时

---

### Phase 13: 测试与优化

**目标**: 实现测试覆盖率达标

**任务列表**:
1. 后端单元测试（pytest）
   - [ ] `backend/tests/conftest.py` - fixtures
   - [ ] `backend/tests/test_student_factory.py`
   - [ ] `backend/tests/test_memory_persistence.py`
   - [ ] `backend/tests/test_teacher_agent.py`
   - [ ] `backend/tests/test_session_orchestrator.py`
   - [ ] 覆盖率 >60%

2. 前端测试（vitest）
   - [ ] `frontend/src/__tests__/hooks/useWebSocket.test.ts`
   - [ ] `frontend/src/__tests__/components/ObservationView.test.tsx`
   - [ ] 覆盖率 >60%

**验收标准**:
- [ ] 后端测试覆盖率 > 60%
- [ ] 前端测试覆盖率 > 60%
- [ ] 所有核心路径有测试
- [ ] 所有测试通过

**预计时间**: 3-4小时

---

## 总预计时间

27-38小时（3-5个工作日，假设每天8小时）

## 依赖关系

```
Phase 1 (数据库)
    ↓
Phase 2 (学生创建) ← 独立，可并行
    ↓
Phase 3 (Memory系统)
    ↓
Phase 4 (教师Agent) ← 独立，可并行
    ↓
Phase 5 (学生Agent) ← 独立，可并行
    ↓
Phase 6 (三种模式)
    ↓
Phase 7 (Orchestrator)
    ↓
Phase 8 (WebSocket)
    ↓
Phase 9 (后端API)
    ↓
Phase 10 (观察模式UI)
    ↓
Phase 11 (分析报告)
    ↓
Phase 12 (教师模式UI)
    ↓
Phase 13 (测试)
```

## 快速开始

**当前进度**: Phase 3 已完成 ✅

✅ **已完成**:
- Phase 1: 基础设施与数据层
- Phase 2: 学生创建系统
  - `backend/core/name_pool.py` - 中文名字池（50个姓氏 + 80个名字 = 4000+组合）
  - `backend/core/student_factory.py` - StudentFactory（三种创建模式）
  - 完整测试覆盖（20个新测试：3个NamePool + 17个StudentFactory）
  - 所有边界情况、可复现性、分布准确性测试通过
- Phase 3: Memory 系统（核心）
  - `backend/agents/memories/session_memory.py` - SessionMemory类（消息历史、教学摘要）
  - `backend/agents/memories/teacher_memory.py` - TeacherAgentMemory类（知识点追踪、学生问题记录）
  - `backend/agents/memories/student_memory.py` - StudentAgentMemory类（学习曲线模拟）
  - `backend/agents/memories/memory_manager.py` - MemoryManager类（消息路由、摘要更新）
  - `backend/agents/memories/memory_persistence.py` - MemoryPersistence类（数据库持久化）
  - 完整测试覆盖（43个新测试：9个SessionMemory + 8个TeacherAgentMemory + 8个StudentAgentMemory + 14个MemoryManager + 4个Summary + 14个Persistence + 2个Integration）
  - 所有保存和加载操作完整测试通过

📋 **下一步**: Phase 4 - 教师 Agent（单个，先做基础）

