# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 检查点系统 API

### 创建检查点计划

创建一个新的教学检查点计划。

```http
POST /checkpoint-plans/
```

**Query 参数:**
- `session_id` (integer, required) - 教学会话 ID

**请求体:**
```json
{
  "topic": "Python 变量与数据类型",
  "teaching_mode": "didactic",
  "checkpoints": [
    {
      "title": "变量基础",
      "key_point": "理解变量的定义和赋值",
      "checkpoint_question": "什么是变量？"
    }
  ]
}
```

**字段说明:**
- `topic` (string) - 教学主题
- `teaching_mode` (string) - 教学模式，可选值：`didactic`（灌输式）、`heuristic`（启发式）、`discussion`（讨论式）、`teacher`（教师）
- `checkpoints` (array) - 检查点列表

**响应示例:**
```json
{
  "plan_id": 1
}
```

---

### 获取检查点计划

获取指定会话的检查点计划。

```http
GET /checkpoint-plans/{session_id}
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**响应示例:**
```json
{
  "topic": "Python 变量与数据类型",
  "teaching_mode": "didactic",
  "checkpoints": [
    {
      "title": "变量基础",
      "key_point": "理解变量的定义和赋值",
      "checkpoint_question": "什么是变量？",
      "state": "pending"
    }
  ],
  "current_index": 0
}
```

**错误响应:**
```json
{
  "detail": "Checkpoint plan for session 1 not found"
}
```
状态码: 404

---

### 更新检查点状态

更新指定检查点的状态。

```http
PUT /checkpoint-plans/{session_id}/checkpoints/{checkpoint_index}/state
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID
- `checkpoint_index` (integer) - 检查点索引（从 0 开始）

**请求体:**
```json
{
  "new_state": "teaching"
}
```

**字段说明:**
- `new_state` (string) - 新状态，可选值：`pending`、`teaching`、`questions`、`complete`

**响应示例:**
```json
{
  "message": "Checkpoint state updated successfully"
}
```

**错误响应:**
```json
{
  "detail": "Invalid state: invalid. Must be one of: pending, teaching, questions, complete"
}
```
状态码: 400

```json
{
  "detail": "Checkpoint plan for session 1 not found"
}
```
状态码: 404

---

### 推进到下一个检查点

将 `current_index` 加 1，并将新当前检查点状态设为 `TEACHING`。

```http
PUT /checkpoint-plans/{session_id}/advance
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**响应示例:**
```json
{
  "topic": "Python 变量与数据类型",
  "teaching_mode": "didactic",
  "checkpoints": [
    {
      "title": "变量基础",
      "key_point": "理解变量的定义和赋值",
      "checkpoint_question": "什么是变量？",
      "state": "complete"
    },
    {
      "title": "数据类型",
      "key_point": "理解基本数据类型",
      "checkpoint_question": "Python 有哪些基本数据类型？",
      "state": "teaching"
    }
  ],
  "current_index": 1
}
```

**错误响应:**
```json
{
  "detail": "Checkpoint plan for session 1 not found"
}
```
状态码: 404

```json
{
  "detail": "Cannot advance beyond last checkpoint"
}
```
状态码: 400

---

### 删除检查点计划

删除指定会话的检查点计划。

```http
DELETE /checkpoint-plans/{session_id}
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**响应示例:**
```json
{
  "message": "Checkpoint plan deleted successfully"
}
```

---

## WebSocket 通信

### WebSocket 端点

实时双向通信端点，支持观察模式和教师模式。

```http
WS /ws/sessions/{session_id}
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**连接建立后收到:**
```json
{
  "type": "connected",
  "session_id": 1
}
```

**心跳机制:**

客户端发送：
```json
{"type": "ping"}
```

服务端返回：
```json
{"type": "pong"}
```

**服务端推送事件:**

| 事件类型 | type 字段 | 说明 |
|---------|-----------|------|
| 消息事件 | `message` | 教师讲授、学生回答等 |
| 检查点状态变更 | `checkpoint_state_change` | 检查点状态切换 |
| 学生回答 | `student_answer` | 教师模式下学生回答实时推送 |
| 会话状态 | `session_state` | 会话整体状态变更 |
| 会话结束 | `session_end` | 教学会话结束 |

**消息事件示例:**
```json
{
  "type": "message",
  "session_id": 1,
  "sender": "teacher",
  "message_type": "lecture",
  "content": "今天我们学习Python变量",
  "receiver": "all"
}
```

**检查点状态变更示例:**
```json
{
  "type": "checkpoint_state_change",
  "session_id": 1,
  "index": 2,
  "checkpoint": {
    "title": "数据类型",
    "key_point": "理解基本数据类型",
    "state": "teaching"
  },
  "progress": {
    "current": 3,
    "total": 5,
    "completed": 2
  }
}
```

**学生回答事件示例（教师模式）:**
```json
{
  "type": "student_answer",
  "session_id": 1,
  "student_name": "张三",
  "content": "一次函数是 y=kx+b",
  "message_type": "answer_to_checkpoint"
}
```

---

## 会话管理 API

### 获取会话消息列表

获取指定会话的所有消息，按时间排序。

```http
GET /sessions/{session_id}/messages
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**响应示例:**
```json
[
  {
    "id": 1,
    "session_id": 1,
    "sender": "teacher",
    "message_type": "lecture",
    "content": "今天我们学习Python变量",
    "receiver": "all",
    "timestamp": "2026-04-07T20:00:00"
  }
]
```

**空列表响应（不存在消息）:**
```json
[]
```
状态码: 200

---

### 获取会话状态

获取指定会话的状态信息。

```http
GET /sessions/{session_id}/status
```

**路径参数:**
- `session_id` (integer) - 教学会话 ID

**响应示例:**
```json
{
  "session_id": 1,
  "topic": "Python 变量与数据类型",
  "created_at": "2026-04-07T20:00:00"
}
```

**错误响应:**
```json
{
  "detail": "会话不存在"
}
```
状态码: 404

---

## 观察模式 API

### 启动观察模式会话

启动观察模式自动教学会话，创建 teaching_session 记录并返回 session_id。

```http
POST /observation/start
```

**请求体:**
```json
{
  "topic": "Python 变量与数据类型",
  "teaching_mode": "heuristic",
  "checkpoint_count": 3,
  "students": [
    {
      "name": "张三",
      "level": "excellent",
      "attitude": "active",
      "learning_ability": 8
    }
  ]
}
```

**字段说明:**
- `topic` (string, required) - 教学主题，最少 1 字符
- `teaching_mode` (string, required) - 教学模式：`didactic`、`heuristic`、`discussion`
- `checkpoint_count` (integer, optional) - 检查点数量，1-10，默认 5
- `students` (array, required, min 1) - 学生列表，不能为空

**响应示例:**
```json
{
  "session_id": 1,
  "status": "running"
}
```

**错误响应:**

缺少必需字段：
```json
{
  "detail": [
    {"loc": ["body", "topic"], "msg": "field required", "type": "value_error.missing"}
  ]
}
```
状态码: 422

空学生列表：
```json
{
  "detail": [
    {"loc": ["body", "students"], "msg": "List should have at least 1 item", "type": "value_error.list.min_length"}
  ]
}
```
状态码: 422

---

## 数据模型

### CheckpointState 枚举

检查点状态：

| 值 | 说明 |
|-----|------|
| `pending` | 待开始 |
| `teaching` | 教学中 |
| `questions` | 提问环节 |
| `complete` | 已完成 |

### Checkpoint 模型

单个检查点教学单元：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `title` | string | 是 | 检查点标题 |
| `key_point` | string | 是 | 本检查点的核心知识点 |
| `checkpoint_question` | string | 是 | 检查理解的问题 |
| `state` | CheckpointState | 否 | 检查点当前状态，默认 `pending` |

### CheckpointPlan 模型

一节课的完整检查点计划：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `topic` | string | 是 | 教学主题 |
| `teaching_mode` | string | 是 | 教学模式 |
| `checkpoints` | array[Checkpoint] | 是 | 检查点列表，至少 1 个 |
| `current_index` | integer | 否 | 当前检查点索引，默认 0 |

---

## 教学模式说明

| 模式 | 代码 | 说明 |
|------|------|------|
| 灌输式 | `didactic` | 连续讲授，无提问 |
| 启发式 | `heuristic` | 讲授后提问 checkpoint 问题 |
| 讨论式 | `discussion` | 频繁提问，引导学生讨论 |
| 教师 | `teacher` | 教师模式，用户手动控制教学 |

---

## 待实现模块

- **学生模块** - 学生创建、管理、导入导出（Phase 10 前端集成时实现）
- **教师模式 API** - 用户手动控制教学（Phase 12 前端 UI 配合实现）
- **观察模式报告** - `GET /observation/{session_id}/report`（Phase 11 分析报告）
