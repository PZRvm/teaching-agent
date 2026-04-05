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

- **学生模块** - 学生创建、管理、导入导出
- **会话模块** - 教学会话管理
- **观察模式 API** - 自动教学流程
- **教师模式 API** - 用户手动控制教学
- **WebSocket 通信** - 实时消息推送
