# 测试目录结构

本项目的测试分为四个目录，按测试类型和是否涉及 LLM 调用分类。

## 目录说明

### `tests/units/` - 单元测试（非 LLM）
纯业务逻辑单元测试，不涉及 LLM 调用或使用 Mock LLM。

**包含测试：**
- `test_checkpoint_persistence*.py` - 检查点持久化测试
- `test_checkpoint_schemas.py` - 检查点数据模型测试
- `test_checkpoint_service.py` - 检查点服务单元测试
- `test_memory_manager.py` - 记忆管理器测试
- `test_name_pool.py` - 姓名池测试
- `test_observation_schemas.py` - 观察模式数据模型测试
- `test_schemas.py` - 通用数据模型测试
- `test_settings.py` - 配置测试
- `test_student_factory.py` - 学生工厂测试

**运行命令：**
```bash
# 运行所有单元测试（非 LLM）
pytest tests/units/ -v

# 运行特定测试文件
pytest tests/units/test_memory_manager.py -v
```

---

### `tests/unit_llm/` - 单元测试（LLM 相关）
测试涉及 LLM 调用的业务逻辑，但使用 Mock LLM（不需要真实 API）。

**包含测试：**
- `test_llm_client.py` - LLM 客户端测试（支持 7B/72B 模型配置）
- `test_llm_utils.py` - LLM 工具函数测试（safe_llm_call）
- `test_teacher_agent.py` - 教师 Agent 单元测试
- `test_student_agent.py` - 学生 Agent 单元测试
- `test_session_orchestrator.py` - 会话编排器单元测试
- `test_teacher_controller.py` - 教师控制器单元测试

**运行命令：**
```bash
# 运行所有 LLM 单元测试（不需要 API key）
pytest tests/unit_llm/ -v

# 运行特定测试
pytest tests/unit_llm/test_llm_client.py -v
```

---

### `tests/integration/` - 集成测试（非 LLM）
集成测试，测试数据库、API、WebSocket 等组件的集成，不涉及真实 LLM 调用。

**包含测试：**
- `test_alembic_migration.py` - 数据库迁移测试
- `test_checkpoint_api.py` - 检查点 API 测试
- `test_database.py` - 数据库连接测试
- `test_memory_persistence.py` - 记忆持久化测试
- `test_observation_api.py` - 观察模式 API 测试
- `test_student_memory_migration.py` - 学生记忆数据模型测试
- `test_teacher_controller_api.py` - 教师控制器 API 测试
- `test_teacher_controller_full_classroom.py` - 完整课堂流程测试
- `test_websocket.py` - WebSocket 测试

**运行命令：**
```bash
# 运行所有集成测试（非 LLM）
pytest tests/integration/ -v -m "not integration"
```

---

### `tests/integration_llm/` - 集成测试（真实 LLM）
使用真实 LLM API 的集成测试，需要配置 API key 和网络连接。

**包含测试：**
- `test_checkpoint_service_real.py` - 检查点服务真实 LLM 测试
- `test_session_orchestrator_full.py` - 会话编排器完整流程测试
- `test_teacher_agent_real.py` - 教师 Agent 真实 LLM 测试
- `test_teacher_controller_real.py` - 教师控制器真实 LLM 测试

**运行命令：**
```bash
# 运行所有真实 LLM 集成测试（需要 API key）
pytest tests/integration_llm/ -v -m integration

# 或运行所有 integration_llm 测试（包括标记和未标记的）
pytest tests/integration_llm/ -v
```

---

## 快速参考

| 测试目录 | 需要 API Key | 需要 Mock | 测试内容 |
|---------|-------------|-----------|---------|
| `tests/units/` | ❌ | ❌ | 纯业务逻辑 |
| `tests/unit_llm/` | ❌ | ✅ | LLM 相关逻辑（Mock） |
| `tests/integration/` | ❌ | ❌ | 数据库/API/WebSocket |
| `tests/integration_llm/` | ✅ | ❌ | 真实 LLM 集成测试 |

## 运行所有测试

```bash
# 运行所有测试（排除需要真实 LLM API 的测试）
pytest tests/ -v -m "not integration"

# 运行所有测试（包括需要真实 LLM API 的测试）
pytest tests/ -v
```

## 测试标记

- `@pytest.mark.integration` - 标记需要真实 LLM API 的集成测试
- `@pytest.mark.asyncio` - 标记异步测试
