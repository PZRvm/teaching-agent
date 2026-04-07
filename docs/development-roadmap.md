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
   - [✓] `backend/agents/memories/session_memory.py` - SessionMemory类
   - [✓] message_history列表
   - [✓] teaching_summary
   - [✓] should_update_summary() 判断逻辑

2. TeacherAgentMemory
   - [✓] `backend/agents/memories/teacher_memory.py` - TeacherAgentMemory类
   - [✓] covered_topics追踪
   - [✓] student_questions字典
   - [✓] student_participation字典
   - [✓] get_system_prompt_addition()

3. StudentAgentMemory
   - [✓] `backend/agents/memories/student_memory.py` - StudentAgentMemory类
   - [✓] learned_concepts - 已掌握概念列表
   - [✓] current_knowledge_level - 当前知识水平（0-1）
   - [✓] should_remember_concept() - 基于学习参数判断是否记住
   - [✓] update_knowledge() - 尝试学习新概念
   - [✓] get_system_prompt_addition() - 生成学生 prompt 上下文

4. MemoryManager
   - [✓] `backend/agents/memories/memory_manager.py` - MemoryManager类
   - [✓] process_message() 方法
   - [✓] _process_lecture() - 提取知识点并更新学生记忆
   - [✓] _check_and_update_summary() - LLM生成摘要
   - [✓] register_student() - 注册学生到记忆系统

5. MemoryPersistence服务
   - [✓] `backend/agents/memories/memory_persistence.py`
   - [✓] _upsert() 通用方法
   - [✓] save_session_memory()
   - [✓] save_teacher_memory()
   - [✓] save_student_memory()
   - [✓] save_message()
   - [✓] load_session_memory()
   - [✓] load_teacher_memory()
   - [✓] load_student_memory()
   - [✓] _load_message_history()

**验收标准**:
- [✓] 消息能添加到message_history
- [✓] 每10条消息触发一次摘要更新（通过测试验证）
- [✓] 会话结束后能从数据库完整恢复所有数据（SessionMemory + TeacherAgentMemory + StudentAgentMemory）
- [✓] StudentAgentMemory 正常持久化和加载
- [✓] 学生学习状态（learned_concepts, knowledge_level）正确保存和恢复
- [✓] 并发更新不丢失数据（测试同时更新）
- [✓] 验证：创建会话→添加消息→持久化→读取恢复

**完成时间**: 2026-04-04

---

### Phase 4: 教师Agent（单个，先做基础）

**目标**: 实现教师Agent的基础功能

**任务列表**:
1. LangChain基础集成
   - [✓] 配置硅基流动API（Qwen2.5-7B-Instruct）
   - [✓] 测试LLM连接

2. MemoryAwareTeacherAgent基础结构
   - [✓] `backend/agents/teacher_agent.py`
   - [✓] __init__ with MemoryManager and LLM
   - [✓] teaching_mode 参数校验（didactic/heuristic/discussion）

3. 讲授功能
   - [✓] deliver_lecture() 方法
   - [✓] deliver_lecture_stream() 流式输出
   - [✓] 根据teaching_mode调整讲授风格（不同 system prompt + temperature）
   - [✓] is_content_complete() LLM 判断内容是否完成

4. LLMClient
   - [✓] `backend/core/llm_client.py` - 封装 ChatOpenAI
   - [✓] invoke() 同步调用
   - [✓] stream() 流式调用
   - [✓] from_config() 从 YAML + .env 配置

5. 测试
   - [✓] 15 个 TeacherAgent 单元测试
   - [✓] 6 个 LLMClient 单元测试
   - [✓] 3 个真实 LLM 集成测试（流式输出）
   - [✓] 8 个错误路径测试（stream/empty/rollback）
   - [✓] 1 个 is_content_complete 标点剥离测试

6. 代码质量改进（gstack review）
   - [✓] safe_llm_call 统一 LLM 错误处理
   - [✓] deliver_lecture 空内容检查
   - [✓] deliver_lecture_stream 异常时不记录部分内容
   - [✓] MemoryPersistence asyncio.Lock 并发安全 + rollback 保护
   - [✓] 时区统一使用 TIMEZONE (Asia/Shanghai)

**验收标准**:
- [✓] 能连接LLM API
- [✓] 能输出讲授内容（lecture）
- [✓] 讲授内容与教学主题相关
- [✓] 验证：调用agent，查看输出内容

**完成时间**: 2026-04-05

---

### Phase 5: 学生Agent（单个）

**目标**: 实现学生Agent的基础功能

**任务列表**:
1. MemoryAwareStudentAgent基础结构
   - [✓] `backend/agents/student_agent.py`
   - [✓] __init__ with StudentAgentMemory and LLM

2. 回答功能
   - [✓] answer_question() 方法
   - [✓] 基于level参数差异化回答质量
   - [✓] 基于attitude参数差异化主动性

3. should_respond() 判断
   - [✓] 积极学生更主动响应
   - [✓] 消极学生响应较少

4. 主动提问与作业（额外实现）
   - [✓] ask_question() — 基于困惑点向教师提问
   - [✓] submit_homework() — 提交作业
   - [✓] give_feedback() — 课程总结性反馈

5. 共享基础设施（额外实现）
   - [✓] `backend/core/settings.py` — 从 YAML 加载配置（timezone、temperature、probability）
   - [✓] `backend/core/llm_utils.py` — safe_llm_call 统一 LLM 错误处理

6. 测试
   - [✓] 32 个 StudentAgent 单元测试
   - [✓] 5 个 safe_llm_call 单元测试
   - [✓] 8 个 TeacherAgent 错误路径测试（stream/empty/error）
   - [✓] 3 个 StudentAgent 空内容处理测试

**验收标准**:
- [✓] 学生能回答问题
- [✓] level=优秀的学生比level=基础的学生回答质量更高
- [✓] attitude=积极的学生更主动（回答更多问题）
- [✓] 验证：创建两个不同level的学生，提问对比

**完成时间**: 2026-04-05

---

### Phase 6: 三种教学模式实现

**目标**: 实现灌输式、启发式、讨论式三种教学模式的差异化

**任务列表**:
1. 灌输式模式
   - [✓] system prompt设计
   - [✓] 连续讲授逻辑
   - [✓] 无互动提问

2. 启发式模式
   - [✓] system prompt设计
   - [✓] 每个检查点讲授后提问
   - [✓] ask_checkpoint_question() 方法

3. 讨论式模式
   - [✓] system prompt设计
   - [✓] 每个检查点讲授后引导讨论
   - [✓] ask_discussion_question() 方法

4. 作业和反馈
   - [✓] assign_homework()
   - [✓] grade_homework() - LLM评价
   - [✓] end_feedback()
   - [✓] reply_to_student() - 回复学生（替代 collect_feedback）

**验收标准**:
- [✓] 灌输式：连续讲授，无提问
- [✓] 启发式：讲授后提问checkpoint问题
- [✓] 讨论式：频繁提问，引导学生讨论
- [✓] 三种模式的system prompt风格明显不同
- [✓] 验证：运行三种模式对比输出风格

**完成时间**: 2026-04-05

---

### Phase 6.5: Checkpoint System（检查点系统）

**目标**: 实现检查点 schema、LLM 计划生成服务和 API 端点

**任务列表**:
1. 检查点 Schemas
   - [✓] `backend/models/checkpoint/schemas.py`
   - [✓] CheckpointState 枚举（PENDING/TEACHING/QUESTIONS/COMPLETE）
   - [✓] Checkpoint 模型（title, key_point, checkpoint_question, state）
   - [✓] CheckpointPlan 模型（topic, teaching_mode: str, checkpoints, current_index）
     - [✓] teaching_mode 使用 `str` 类型，教师模式传值 `"teacher"`（非 None）

2. CheckpointPlanService
   - [✓] `backend/models/checkpoint/service.py`
   - [✓] generate_plan() — LLM 调用生成完整检查点计划
   - [✓] LLM prompt 设计（按教学模式调整详细程度）
   - [✓] 三层降级失败处理：
     - [✓] Layer 1: `with_structured_output(CheckpointPlan)` → Pydantic 对象
     - [✓] Layer 2: `Pydantic.model_validate_json(raw)` → 手动解析 LLM 原始输出
     - [✓] Layer 3: 返回最小 1 检查点计划覆盖整个主题
   - [ ] 前端等待动画：生成期间显示 loading spinner + 提示文字（10-30 秒等待）(待前端实现)

3. 检查点持久化
   - [✓] 新建 `checkpoint_plans` 独立表（session_id 外键 → teaching_sessions.id，plan_data JSON 列）
   - [✓] `CheckpointPlanModel` ORM（`backend/orm/checkpoint_plan.py`）
   - [✓] Alembic migration（003_create_checkpoint_plans_table）
   - [✓] `CheckpointPlanPersistence` 服务（`backend/models/checkpoint/persistence_service.py`）
   - [✓] 状态变更时更新该字段
   - [✓] 并发安全（with_for_update() 行锁）

4. 检查点 API 端点
   - [✓] POST /checkpoint-plans/ — 创建检查点计划
   - [✓] GET /checkpoint-plans/{session_id} — 获取检查点计划
   - [✓] PUT /checkpoint-plans/{session_id}/checkpoints/{index}/state — 更新检查点状态
   - [✓] PUT /checkpoint-plans/{session_id}/advance — 推进到下一个检查点（额外实现）
   - [✓] DELETE /checkpoint-plans/{session_id} — 删除检查点计划（额外实现）

5. 测试（详细测试清单）
   - [✓] CheckpointState 枚举值验证（4 个状态）
   - [✓] Checkpoint 模型创建 + 默认 state=PENDING
   - [✓] CheckpointPlan 模型创建 + 默认 current_index=0
   - [✓] CheckpointPlan.teaching_mode 接受 4 个值（didactic/heuristic/discussion/teacher）
   - [✓] generate_plan() — 正常生成（Mock LLM 返回有效 JSON）
   - [✓] generate_plan() — Layer 1 失败 → 降级到 Layer 2
   - [✓] generate_plan() — Layer 2 也失败 → 降级到 Layer 3（1 检查点）
   - [✓] generate_plan() — 空检查点列表 → Layer 3 兜底
   - [✓] generate_plan() — 不同教学模式生成不同详细程度
   - [✓] generate_plan() — teaching_mode="teacher" 时正常工作
   - [✓] API POST /checkpoint-plans/ — 200 + 有效响应
   - [✓] API POST /checkpoint-plans/ — 缺少参数 → 422
   - [✓] API GET /checkpoint-plans/{session_id} — 200
   - [✓] API GET /checkpoint-plans/{session_id} — 不存在 → 404
   - [✓] API PUT /checkpoint-plans/{session_id}/checkpoints/{index}/state — 200
   - [✓] API PUT /checkpoint-plans/{session_id}/advance — 200
   - [✓] 持久化 — 生成后存储到 checkpoint_plans 独立表
   - [✓] 持久化 — 状态更新后 JSON 字段正确更新
   - [✓] CheckpointPlan JSON 序列化/反序列化往返测试
   - [✓] 灌输式模式跳过 QUESTIONS 状态验证
   - [✓] 并发安全测试（with_for_update 行锁测试）

**验收标准**:
- [✓] 输入主题和教学模式，返回结构化的 CheckpointPlan
- [✓] 每个检查点包含 title, key_point, checkpoint_question
- [✓] 灌输式/启发式/讨论式生成的检查点详细程度不同
- [✓] LLM 返回格式错误时三层降级正常工作
- [✓] API 端点正常工作
- [✓] CheckpointPlan 持久化到 checkpoint_plans 独立表
- [✓] teaching_mode="teacher" 在教师模式下正常工作

**详细设计**: `docs/designs/pangzerui-main-design-20260405-203128.md`
**工程评审**: 已通过 gstack review，修复并发问题（行锁 + 错误处理）

**完成时间**: 2026-04-06
**测试覆盖**: 75 个测试全部通过（17 单元测试 + 6 集成测试）

---

### Phase 7: SessionOrchestrator（观察模式核心）✓

**目标**: 实现观察模式的自动教学流程编排（基于检查点）

**任务列表**:
1. SessionOrchestrator基础结构
   - [✓] `backend/models/session/orchestrator.py`
   - [✓] __init__ with teacher_agent, student_agents, checkpoint_plan

2. run_autonomous_session() 主循环（基于检查点）
   - [✓] 遍历检查点数组（替代 is_content_complete() 循环）
   - [✓] is_content_complete() 保留为后备验证（每个检查点完成后可选调用）
   - [✓] 根据teaching_mode调用不同方法

3. 检查点驱动教学
   - [✓] _teach_checkpoint() — 状态机驱动（TEACHING → QUESTIONS → COMPLETE）
   - [✓] _deliver_checkpoint_lecture() — 将 checkpoint.key_point 注入教师 agent system prompt
   - [✓] _handle_checkpoint_questions() — 可取消的协程（支持 asyncio.Task.cancel()）
   - [✓] _trigger_observer_learning_for_checkpoint() — 检查点完成后记录知识点到 MemoryManager
   - [✓] _ws_push_checkpoint_state() — WebSocket 推送检查点状态变更

4. 对话循环（场景 A / 场景 B）
   - [✓] _teacher_question_dialogue_loop() — 场景 A: 教师提问，双方均可结束（至少一轮后）
   - [✓] _student_question_dialogue_loop() — 场景 B: 学生提问，双方均可结束（至少一轮后）
   - [✓] _collect_student_answers() — 收集学生回答，返回 (学生, 回答内容) 列表
   - [✓] _designate_student() — 无人回答时随机指定学生
   - [✓] _single_student_answer() — 让被指定学生回答
   - [✓] _trigger_observer_learning() — 旁听学生概率性学习（update_knowledge）
   - [✓] max_rounds=10 防止无限循环

5. 作业和反馈流程
   - [✓] _assign_homework()（只在最后一个检查点之后）
   - [✓] _collect_homework_and_feedback()

6. 观察模式 API
   - [✓] `backend/models/observation/router.py` — POST /observation/start, GET /observation/{id}/report
   - [✓] `backend/models/observation/schemas/` — ObservationConfig, ObservationStartResponse, metrics, report

7. WebSocket 端点
   - [✓] `backend/models/session/router_websocket.py` — ws/{session_id}
   - [✓] checkpoint_state_change 事件推送

8. 前置修改
   - [✓] Message schema 添加 receiver 字段（默认 "all"）

**验收标准**:
- [✓] 能自动运行完整教学流程（基于检查点）
- [✓] 遍历完所有检查点后自动结束
- [✓] 灌输式跳过 QUESTIONS 状态
- [✓] 检查点状态变更通过 WebSocket 实时推送
- [✓] 能布置作业和收集反馈（最后一个检查点之后）
- [✓] 双方均可结束对话（至少一轮完成后）
- [✓] 旁听学生概率性学习触发
- [✓] 检查点完成后 key_point 记录到 MemoryManager
- [✓] 验证：创建观察会话，自动运行到结束

**详细计划**: `docs/superpowers/plans/2026-04-05-session-orchestrator.md`
**检查点设计**: `docs/designs/pangzerui-main-design-20260405-203128.md`

**完成时间**: 2026-04-06
**测试覆盖**: 245 个测试通过（241 单元测试 + 4 集成测试）

---

### Phase 7.5: TeacherSessionController（教师模式核心）✓

**目标**: 实现教师模式的后端编排逻辑，将用户操作分发给学生 agents（支持检查点）

**任务列表**:
1. TeacherSessionController 基础结构
   - [✓] `backend/models/session/teacher_controller.py`
   - [✓] __init__ with student_agents, memory_manager, checkpoint_plan
   - [✓] _active_dialogue 状态追踪

2. 用户操作处理方法
   - [✓] handle_broadcast_lecture() — 广播讲授内容给全体学生
   - [✓] handle_ask_to_all() — 向全体提问，收集回答
   - [✓] handle_ask_to_student() — 向指定学生提问（用户主动选择）
   - [✓] handle_teacher_reply() — 用户回复学生（场景 A 对话循环）
   - [✓] handle_end_dialogue() — 用户主动结束对话，触发旁听学习

3. 检查点操作方法
   - [✓] handle_edit_checkpoints() — 真人教师编辑检查点计划（开始前）
   - [✓] handle_advance_checkpoint() — 手动跳转到下一个检查点
   - [✓] _force_end_current_dialogue() — 强制结束当前对话，三个清理步骤：
     1. 取消学生 agent 正在进行的 LLM 调用（asyncio.Task.cancel()）
     2. 回滚 MemoryManager 中本检查点的部分状态（如未完成的参与记录）
     3. 推送 checkpoint_state_change WebSocket 事件通知前端
   - [✓] _advance_to_next_pending() — 前进到下一个 PENDING 检查点

4. 作业和结束流程
   - [✓] handle_assign_homework() — 布置作业，收集提交，LLM 评分（最后一个检查点之后）
   - [✓] handle_end_teaching() — 结束教学，收集学生反馈

5. 对话状态管理
   - [✓] 至少一轮对话完成后才能结束（与观察模式相同的约束）
   - [✓] 旁听学习：对话结束后触发 update_knowledge（复用观察模式逻辑）
   - [✓] _handle_checkpoint_questions() 必须实现为可取消的协程（except asyncio.CancelledError）

6. 检查点 API
   - [✓] GET /checkpoint-plan/{session_id} — 获取检查点计划
   - [✓] PUT /checkpoint-plan/{session_id} — 编辑检查点计划
   - [✓] POST /sessions/{session_id}/advance-checkpoint — 手动推进

**与 Phase 7（观察模式）的区别**:
- 教师模式没有 TeacherAgent，教师由用户扮演
- 教师模式不需要选择教学模式，用户自行决定教学方式
- 学生指定由用户手动操作，而非随机选择
- 教学节奏由用户控制 + 检查点结构（可手动推进）
- 对话结束由用户主动触发（end_dialogue 指令）
- 用户可在上课前编辑检查点计划

**验收标准**:
- [✓] 用户能编辑检查点计划（标题/知识点/示例/问题）
- [✓] 用户能手动推进到下一个检查点，强制结束当前互动
- [✓] 用户能广播讲授内容给全体学生
- [✓] 用户能向全体提问并收集回答
- [✓] 用户能指定某个学生回答问题
- [✓] 用户能与指定学生进行多轮对话
- [✓] 至少一轮后才能结束对话
- [✓] 对话结束后旁听学生触发学习
- [✓] 用户能布置作业并收到 LLM 评分
- [✓] 用户能结束教学并收到学生反馈

**详细计划**: `docs/superpowers/plans/2026-04-06-teacher-controller.md`
**检查点设计**: `docs/designs/pangzerui-main-design-20260405-203128.md`

**完成时间**: 2026-04-07
**测试覆盖**: 193 个测试通过（125 单元 LLM 测试 + 48 集成测试 + 20 其他）

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
   - [ ] 已进行时间显示
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
   - [ ] 配置界面（复用StudentFactory，不需要选择教学模式）
   - [ ] "开始教学"按钮

2. TeacherView组件
   - [ ] 用户输入区域（讲授、提问、回复）
   - [ ] 学生选择器（指定学生回答）
   - [ ] 学生响应显示
   - [ ] 消息列表（复用）

**验收标准**:
- [ ] 能配置并开始教师模式（无需选择教学模式）
- [ ] 能输入教学内容和问题
- [ ] 能选择指定学生回答问题
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

30-42小时（3-5个工作日，假设每天8小时）

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
Phase 6.5 (Checkpoint System - 检查点系统)
    ↓
Phase 7 (Orchestrator - 观察模式，基于检查点)
    ↓
Phase 7.5 (TeacherController - 教师模式，检查点编辑/推进)
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

**当前进度**: Phase 6.5/7 进行中（检查点系统设计已完成，待实施），Phase 7.5 设计已完成（待制作详细计划）

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
  - `backend/agents/memories/memory_persistence.py` - MemoryPersistence类（数据库持久化，asyncio.Lock 并发安全）
  - 完整测试覆盖（43个新测试：9个SessionMemory + 8个TeacherAgentMemory + 8个StudentAgentMemory + 14个MemoryManager + 4个Summary + 14个Persistence + 2个Integration）
  - 所有保存和加载操作完整测试通过
- Phase 4: 教师 Agent
  - `backend/core/llm_client.py` - LLMClient（封装 ChatOpenAI，支持 invoke/stream）
  - `backend/agents/teacher_agent.py` - TeacherAgent（讲授、流式输出、内容完成判断）
  - 三种教学模式支持（didactic/heuristic/discussion），不同 prompt + temperature
  - `backend/core/settings.py` - 从 YAML 加载配置（timezone、temperature、probability）
  - `backend/core/llm_utils.py` - safe_llm_call 统一 LLM 错误处理
  - 并发安全（asyncio.Lock）+ 错误处理（rollback、空内容检查、stream 异常保护）
  - 完整测试覆盖（34个测试：23个TeacherAgent + 6个LLMClient + 5个safe_llm_call）
  - 160 个测试全部通过
- Phase 5: 学生 Agent
  - `backend/agents/student_agent.py` - StudentAgent（回答问题、主动提问、提交作业、课程反馈）
  - 基于 level 参数差异化回答质量（_LEVEL_INSTRUCTIONS）
  - 基于 attitude 参数差异化响应概率（STUDENT_RESPOND_PROBABILITIES）
  - 完整测试覆盖（35个新测试：32个StudentAgent + 3个空内容处理）
  - 160 个测试全部通过
- Phase 6: 三种教学模式实现
  - `backend/agents/teacher_agent.py` - 新增三种教学模式差异化逻辑
  - `_MODE_INSTRUCTIONS` 定义 didactic/heuristic/discussion 三种 system prompt 风格
  - `ask_checkpoint_question()` / `ask_discussion_question()` / `reply_to_student()` /
    `assign_homework()` / `grade_homework()` / `end_feedback()` 方法实现
  - `backend/agents/memories/memory_manager.py` - 补全所有 MessageType 分支处理
  - `backend/tests/units/test_teacher_agent.py` - 新增 40 个测试（共 200 个单测）
  - 所有新方法均有正常路径和错误路径测试覆盖

📝 **设计文档更新**:
- `docs/design.md` - Agent Interaction Flow 章节
  - 核心规则: 双方均可结束对话（至少一轮完成后）
  - 场景 A: 教师提问 → 双方可结束
  - 场景 B: 学生提问 → 双方可结束
  - 旁听学习: 对话结束后概率性触发 update_knowledge
  - 指定学生机制: 观察模式随机选择 / 教师模式用户手动指定
  - Message Type Flow Matrix: 对话结束权统一为"双方（至少一轮后）"
- `docs/design.md` - Teacher Mode Architecture 章节（新增）
  - 核心区别: 用户替代 TeacherAgent 的决策角色
  - 6 种用户操作类型: broadcast_lecture / ask_question_to_all / ask_question_to_student / teacher_reply / end_dialogue / end_teaching
  - WebSocket 消息协议定义
  - TeacherSessionController 后端编排器设计
  - 场景 A/B 在教师模式下的差异说明
- `docs/design.md` - Checkpoint-Based Teaching Flow 章节（新增）
  - 检查点状态机: PENDING → TEACHING → QUESTIONS → COMPLETE
  - Checkpoint / CheckpointPlan schema 定义
  - CheckpointPlanService LLM 计划生成
  - SessionOrchestrator 从 is_content_complete() 重构为检查点迭代
  - 教师模式检查点编辑和手动推进
  - WebSocket checkpoint_state_change 事件
  - 检查点 API 端点
  - 观察模式/教师模式检查点流程图
- `docs/design.md` - System Flow Overview 更新
  - 教师模式流程增加 LLM 生成检查点 + 编辑步骤
  - 观察模式流程增加 LLM 生成检查点 + 检查点进度显示
- `docs/design.md` - Phase Transitions 更新
  - 从三种教学模式独立循环重构为统一的检查点循环
- `docs/designs/pangzerui-main-design-20260405-203128.md`（新增）
  - 完整的检查点系统设计文档（由 /office-hours 生成）

📋 **下一步**:
- Phase 6.5 - Checkpoint System 实施（schemas + CheckpointPlanService + API）
- Phase 7 - SessionOrchestrator 实施（计划已完成，基于检查点重构）
- Phase 7.5 - TeacherSessionController 实施（设计已完成，待制作详细计划）

