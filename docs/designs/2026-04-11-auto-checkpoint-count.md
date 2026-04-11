# 设计文档: 移除用户指定检查点数量，改为 LLM 自动决定

生成时间: 2026-04-11
分支: feature/observation-frontend
状态: APPROVED
模式: Builder

## 问题陈述

当前检查点数量由用户在前端界面手动输入（1-10，默认5）。这个设计决策有几个问题:

1. 用户不一定知道一个教学主题适合多少个检查点
2. 额外的配置步骤增加了认知负担
3. LLM 更了解主题的复杂度，应该由它来决定

改动目标: 移除用户指定检查点数量的环节，让 LLM 根据教学主题自动决定生成多少个检查点，系统提示词中加"最多 10 个"约束。

## 约束

- 7B 模型上下文窗口 32K，检查点数量过多会导致上下文溢出（已有先例）
- 最多 10 个检查点的硬约束
- 前端步骤从 4 步简化为 3 步

## 前提

1. LLM 能根据主题复杂度自动决定合理的检查点数量
2. 最多 10 个检查点的硬约束足够（结合上下文溢出修复）
3. 前端步骤 2.5 直接移除，不再显示检查点数量输入

## 改动范围

### 后端文件（5 个）

#### 1. `backend/models/checkpoint/service.py`

**`_build_prompt()` 方法**:

当前 (第 77-100 行):
```python
return f"""请为主题 "{topic}" 生成一个包含 {checkpoint_count} 个检查点的教学计划。
...
```

改为:
```python
return f"""请为主题 "{topic}" 生成一个教学计划。

请根据主题的复杂度和知识量，自行决定需要多少个检查点。
要求:
- 每个检查点涵盖一个核心知识点
- 检查点数量最多 10 个
- 简单主题 3-5 个，复杂主题 5-8 个

教学模式: {teaching_mode}
{mode_instruction}
...
"""
```

**`generate_plan()` 方法**: 去掉 `checkpoint_count` 参数。

```python
async def generate_plan(
    self, topic: str, teaching_mode: str
) -> CheckpointPlan:
```

#### 2. `backend/models/observation/schemas.py`

**`ObservationConfig`**: 删除 `checkpoint_count` 字段。

```python
class ObservationConfig(BaseModel):
    topic: str
    teaching_mode: str
    students: list[StudentProfile]
```

#### 3. `backend/models/observation/router.py`

**`_run_orchestrator_background()`**: 不再传递 `checkpoint_count`。

#### 4. `backend/models/observation/service.py`

**`_run_background_task()`**: 不再接收和传递 `checkpoint_count`。
**`_generate_checkpoint_plan()`**: 不再传递数量给 `generate_plan()`。

#### 5. `backend/models/checkpoint/router.py`

无需修改。该文件端点不直接使用 `checkpoint_count`。

#### 6. `docs/api.md`

移除 `POST /observation/start` 文档中的 `checkpoint_count` 参数说明。

### 前端文件（3 个）

#### 7. `frontend/src/views/ObservationConfig.tsx`

- 删除 `checkpointCount` state（约第 302-310 行的步骤 2.5）
- 删除步骤 2.5 的整个 `<section className="step-card">` 块
- 步骤号从 1, 2, 2.5, 3 改为 1, 2, 3
- `startObservation()` 调用中删除 `checkpoint_count` 参数

#### 8. `frontend/src/types/observation.ts`

删除 `checkpoint_count` 字段:

```typescript
// 删除这一行:
checkpoint_count?: number
```

#### 9. `frontend/src/apis/observation.ts`

`startObservation` 函数不再发送 `checkpoint_count`。

### 测试文件

需要更新引用了 `checkpoint_count` 的测试:

- `frontend/tests/views/ObservationConfig.test.tsx` - 移除检查点数量相关的测试用例
- `backend/tests/` 中引用 `checkpoint_count` 的测试

### 错误处理

- `generate_plan()` 已有三层降级机制（完整生成 → 简化生成 → 单检查点兜底）
- LLM 返回的检查点列表如果为空或生成失败，降级机制会处理
- 提示词中约束"最多 10 个"，信任 LLM 遵守，不在代码层做额外截断

## 推荐方案

方案 A: 精简改动。完全移除 `checkpoint_count` 字段，LLM 提示词中加"最多 10 个"约束。

理由: 最小改动，最干净。用户不需要关心检查点数量，LLM 更擅长判断主题复杂度。

## 下一步

1. 后端: 修改 `checkpoint/service.py` 的提示词和 `generate_plan()` 签名
2. 后端: 修改 `observation/schemas.py` 删除 `checkpoint_count`
3. 后端: 修改 `observation/router.py` 和 `service.py` 不传递数量
4. 前端: 修改 `ObservationConfig.tsx` 删除步骤 2.5
5. 前端: 修改 `types/observation.ts` 和 `apis/observation.ts`
6. 更新测试
