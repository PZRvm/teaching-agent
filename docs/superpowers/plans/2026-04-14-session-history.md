# 课堂历史记录 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现课堂历史记录功能，让用户可以浏览已完成的会话列表并查看每节课的详细消息时间线和检查点进度。包括后端会话生命周期修复、会话列表 API、前端历史列表页和详情页。

**Architecture：** 后端在观察模式后台任务中添加会话结束时的 status/end_time/duration 更新逻辑，新增 `GET /sessions/` 列表接口（LEFT JOIN checkpoint_plans）。前端新增 SessionHistory 列表页和 SessionDetail 详情页，使用 rough-design-skill 手绘风格，复用已有 PageNav、RoughBadge、RoughButton 等组件。

**Tech Stack：** Python (FastAPI, SQLAlchemy, Pydantic), pytest + pytest-asyncio, React + TypeScript + styled-components, Vitest + React Testing Library

---

## 文件结构（File Structure）

本计划会创建/修改的文件如下：

**修改（Modify）- 后端：**
- `backend/models/observation/service.py` -- `_run_background_task` 中添加会话生命周期管理（status/end_time/duration 更新）
- `backend/models/session/router.py` -- 新增 `GET /sessions/` 列表接口

**新增（New）- 后端：**
- `backend/tests/units/test_session_list.py` -- 会话列表 API 单元测试

**修改（Modify）- 前端：**
- `frontend/src/apis/session.ts` -- 新增 `SessionSummary`、`CheckpointProgress` 类型和 `getSessionList()` 函数
- `frontend/src/App.tsx` -- 注册 `/history` 和 `/history/:sessionId` 路由
- `frontend/src/views/LandingPage.tsx` -- 启用历史按钮，添加导航

**新增（New）- 前端：**
- `frontend/src/views/SessionHistory.tsx` -- 历史记录列表页
- `frontend/src/views/SessionDetail.tsx` -- 会话详情页

---

## 任务 1：会话生命周期管理（后端前置任务）

目标：在观察模式后台任务结束后，更新 teaching_sessions 表的 status、end_time、duration_seconds 字段。这是历史功能的前置条件。

**相关文件：**
- 修改：`backend/models/observation/service.py:185-191`（finally 块）
- 新建：`backend/tests/units/test_session_lifecycle.py`

- [ ] **Step 1：编写会话生命周期管理的失败测试**

新建 `backend/tests/units/test_session_lifecycle.py`：

```python
"""会话生命周期管理单元测试."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from orm.teaching_session import TeachingSessionModel


@pytest.mark.asyncio
class TestSessionLifecycle:
    """会话生命周期更新测试."""

    async def test_finalize_session_sets_completed_status(self, db_session, test_engine):
        """finalize_session 应设置 status 为 completed."""
        # 创建测试会话
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.flush()

        # 导入并调用 finalize_session
        from models.observation.service import finalize_session

        await finalize_session(
            db=db_session,
            session_id=session.id,
            status="completed",
        )

        await db_session.refresh(session)
        assert session.status == "completed"
        assert session.end_time is not None
        assert session.duration_seconds is not None

    async def test_finalize_session_sets_interrupted_status(self, db_session, test_engine):
        """finalize_session 应设置 status 为 interrupted."""
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.flush()

        from models.observation.service import finalize_session

        await finalize_session(
            db=db_session,
            session_id=session.id,
            status="interrupted",
        )

        await db_session.refresh(session)
        assert session.status == "interrupted"

    async def test_finalize_session_calculates_duration(self, db_session, test_engine):
        """finalize_session 应正确计算 duration_seconds."""
        start = datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
        session = TeachingSessionModel(
            topic="Python 基础",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}],
            status="running",
            start_time=start,
        )
        db_session.add(session)
        await db_session.flush()

        from models.observation.service import finalize_session

        await finalize_session(
            db=db_session,
            session_id=session.id,
            status="completed",
        )

        await db_session.refresh(session)
        assert session.duration_seconds is not None
        assert session.duration_seconds >= 0

    async def test_finalize_session_nonexistent_id_raises(self, db_session, test_engine):
        """finalize_session 对不存在的 session_id 应抛出 ValueError."""
        from models.observation.service import finalize_session

        with pytest.raises(ValueError, match="会话不存在"):
            await finalize_session(
                db=db_session,
                session_id=99999,
                status="completed",
            )
```

- [ ] **Step 2：运行测试验证失败**

Run: `cd backend && pytest tests/units/test_session_lifecycle.py -v`
Expected: FAIL — `ImportError: cannot import name 'finalize_session'`

- [ ] **Step 3：实现 finalize_session 函数**

在 `backend/models/observation/service.py` 顶部添加导入（在已有导入之后）：

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
```

在文件末尾（`_run_background_task` 函数之后）添加：

```python
async def finalize_session(
    *,
    db,
    session_id: int,
    status: str,
) -> None:
    """更新会话的结束状态.

    Args:
        db: 数据库会话
        session_id: 会话 ID
        status: 结束状态（"completed" 或 "interrupted"）
    """
    result = await db.execute(
        select(TeachingSessionModel).where(TeachingSessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"会话不存在 (session_id={session_id})")

    session.status = status
    session.end_time = datetime.now(ZoneInfo("Asia/Shanghai"))
    if session.start_time and session.end_time:
        session.duration_seconds = int(
            (session.end_time - session.start_time).total_seconds()
        )
    await db.commit()
```

- [ ] **Step 4：运行测试验证通过**

Run: `cd backend && pytest tests/units/test_session_lifecycle.py -v`
Expected: 4 passed

- [ ] **Step 5：在 _run_background_task 的 finally 块中调用 finalize_session**

修改 `backend/models/observation/service.py` 中 `_run_background_task` 的 finally 块（约 185-191 行）：

将原来的：
```python
    finally:
        # 8. 清理资源
        orchestrator = registry.get_orchestrator(session_id)
        if orchestrator is not None:
            await orchestrator.stop()
        registry.unregister(session_id)
        logger.info("观察模式会话已清理 (session_id=%d)", session_id)
```

改为：
```python
    finally:
        # 8. 清理资源
        orchestrator = registry.get_orchestrator(session_id)
        if orchestrator is not None:
            await orchestrator.stop()
        registry.unregister(session_id)

        # 9. 更新会话生命周期状态
        async with async_session_maker() as db:
            await finalize_session(
                db=db,
                session_id=session_id,
                status="completed",
            )

        logger.info("观察模式会话已清理 (session_id=%d)", session_id)
```

同时，在 `except` 块中添加中断状态更新（约 166-183 行）。将 except 块末尾改为：

```python
    except Exception as e:
        logger.error(
            "观察模式后台任务失败 (session_id=%d): %s",
            session_id,
            e,
            exc_info=True,
        )
        # 推送错误状态
        with contextlib.suppress(Exception):
            await cm.broadcast(
                session_id,
                {
                    "type": "session_state",
                    "session_id": session_id,
                    "status": "error",
                    "message": "Session initialization failed",
                },
            )
        # 标记会话为中断
        with contextlib.suppress(Exception):
            async with async_session_maker() as db:
                await finalize_session(
                    db=db,
                    session_id=session_id,
                    status="interrupted",
                )
```

- [ ] **Step 6：运行全部测试确认无回归**

Run: `cd backend && pytest tests/units/ -v`
Expected: 全部通过（原有测试不受影响）

- [ ] **Step 7：提交**

```bash
git add backend/models/observation/service.py backend/tests/units/test_session_lifecycle.py
git commit -m "feat(observation): 会话结束时更新 status/end_time/duration"
```

---

## 任务 2：会话列表 API

目标：实现 `GET /sessions/` 接口，返回所有会话列表，按 start_time 倒序，LEFT JOIN checkpoint_plans 计算检查点进度。

**相关文件：**
- 修改：`backend/models/session/router.py`
- 新建：`backend/tests/units/test_session_list.py`

- [ ] **Step 1：编写会话列表 API 的失败测试**

新建 `backend/tests/units/test_session_list.py`：

```python
"""会话列表 API 单元测试."""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from orm.checkpoint_plan import CheckpointPlanModel
from orm.teaching_session import TeachingSessionModel


@pytest.mark.asyncio
class TestSessionListAPI:
    """GET /sessions/ 接口测试."""

    async def test_empty_list_returns_empty_array(self, db_session, test_engine):
        """没有会话时返回空数组."""
        from httpx import ASGITransport, AsyncClient

        from core.app import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/sessions/")

        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_sessions_with_checkpoint_progress(self, db_session, test_engine):
        """有会话和检查点计划时，返回完整数据."""
        # 创建会话
        session = TeachingSessionModel(
            topic="Python 变量",
            teaching_mode="heuristic",
            students_config=[{"name": "张三"}, {"name": "李四"}],
            status="completed",
            start_time=datetime(2026, 4, 12, 14, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            end_time=datetime(2026, 4, 12, 15, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            duration_seconds=3600,
        )
        db_session.add(session)
        await db_session.flush()

        # 创建检查点计划
        plan = CheckpointPlanModel(
            session_id=session.id,
            plan_data={
                "topic": "Python 变量",
                "teaching_mode": "heuristic",
                "current_index": 2,
                "checkpoints": [
                    {"title": "变量介绍", "state": "complete"},
                    {"title": "数据类型", "state": "complete"},
                    {"title": "运算符", "state": "teaching"},
                    {"title": "控制流", "state": "pending"},
                ],
            },
        )
        db_session.add(plan)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.app import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/sessions/")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

        item = data[0]
        assert item["id"] == session.id
        assert item["topic"] == "Python 变量"
        assert item["teaching_mode"] == "heuristic"
        assert item["student_count"] == 2
        assert item["checkpoint_progress"]["total"] == 4
        assert item["checkpoint_progress"]["completed"] == 2
        assert item["checkpoint_progress"]["current_index"] == 2

    async def test_session_without_checkpoint_plan_returns_null_progress(
        self, db_session, test_engine
    ):
        """没有检查点计划的会话返回 checkpoint_progress 为 null."""
        session = TeachingSessionModel(
            topic="函数基础",
            teaching_mode="didactic",
            students_config=[{"name": "王五"}],
            status="interrupted",
            start_time=datetime(2026, 4, 13, 10, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        )
        db_session.add(session)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.app import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/sessions/")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["checkpoint_progress"] is None

    async def test_sessions_ordered_by_start_time_desc(self, db_session, test_engine):
        """会话按 start_time 倒序排列."""
        for i, (topic, hour) in enumerate([("早期课", 8), ("晚期课", 16)]):
            session = TeachingSessionModel(
                topic=topic,
                teaching_mode="didactic",
                students_config=[],
                status="completed",
                start_time=datetime(2026, 4, 12, hour, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            )
            db_session.add(session)
        await db_session.commit()

        from httpx import ASGITransport, AsyncClient

        from core.app import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/sessions/")

        data = resp.json()
        assert len(data) == 2
        assert data[0]["topic"] == "晚期课"
        assert data[1]["topic"] == "早期课"
```

- [ ] **Step 2：运行测试验证失败**

Run: `cd backend && pytest tests/units/test_session_list.py -v`
Expected: FAIL — 返回 404 或其他错误（`/sessions/` 路由不存在）

- [ ] **Step 3：实现会话列表 API**

修改 `backend/models/session/router.py`，在文件顶部添加导入：

```python
from sqlalchemy import select, outerjoin
```

在已有路由之后，添加新的列表路由：

```python
@router.get("/", summary="获取会话列表")
async def get_session_list(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """获取所有会话列表，按开始时间倒序.

    Returns:
        会话列表，包含基本信息和检查点进度
    """
    from orm.checkpoint_plan import CheckpointPlanModel

    # LEFT JOIN 查询会话和检查点计划
    stmt = (
        select(TeachingSessionModel, CheckpointPlanModel.plan_data)
        .outerjoin(
            CheckpointPlanModel,
            TeachingSessionModel.id == CheckpointPlanModel.session_id,
        )
        .order_by(TeachingSessionModel.start_time.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for session, plan_data in rows:
        # 计算学生数量
        student_count = len(session.students_config) if session.students_config else 0

        # 计算检查点进度
        checkpoint_progress = None
        if plan_data is not None:
            checkpoints = plan_data.get("checkpoints", [])
            total = len(checkpoints)
            completed = sum(
                1 for cp in checkpoints if cp.get("state") == "complete"
            )
            checkpoint_progress = {
                "total": total,
                "completed": completed,
                "current_index": plan_data.get("current_index", 0),
            }

        items.append(
            {
                "id": session.id,
                "topic": session.topic,
                "teaching_mode": session.teaching_mode,
                "status": session.status,
                "start_time": (
                    session.start_time.isoformat() if session.start_time else None
                ),
                "end_time": (
                    session.end_time.isoformat() if session.end_time else None
                ),
                "duration_seconds": session.duration_seconds,
                "student_count": student_count,
                "checkpoint_progress": checkpoint_progress,
            }
        )

    return items
```

- [ ] **Step 4：运行测试验证通过**

Run: `cd backend && pytest tests/units/test_session_list.py -v`
Expected: 4 passed

- [ ] **Step 5：代码质量检查**

Run: `cd backend && ruff check models/session/router.py && ruff format models/session/router.py`
Expected: 无错误

- [ ] **Step 6：提交**

```bash
git add backend/models/session/router.py backend/tests/units/test_session_list.py
git commit -m "feat(session): 新增 GET /sessions/ 会话列表接口"
```

---

## 任务 3：前端 API 层

目标：在 `frontend/src/apis/session.ts` 中新增 `SessionSummary`、`CheckpointProgress` 类型和 `getSessionList()` 函数。

**相关文件：**
- 修改：`frontend/src/apis/session.ts`

- [ ] **Step 1：添加会话列表 API 类型和函数**

在 `frontend/src/apis/session.ts` 文件末尾添加：

```typescript
/** 会话检查点进度 */
export interface CheckpointProgress {
  total: number
  completed: number
  current_index: number
}

/** 会话列表项 */
export interface SessionSummary {
  id: number
  topic: string
  teaching_mode: string
  status: string
  start_time: string
  end_time: string | null
  duration_seconds: number | null
  student_count: number
  checkpoint_progress: CheckpointProgress | null
}

/** 获取历史会话列表 */
export async function getSessionList(): Promise<SessionSummary[]> {
  const { data } = await api.get<SessionSummary[]>('/sessions/')
  return data
}
```

- [ ] **Step 2：提交**

```bash
git add frontend/src/apis/session.ts
git commit -m "feat(api): 新增 SessionSummary 类型和 getSessionList 函数"
```

---

## 任务 4：前端 SessionHistory 列表页

目标：实现历史记录列表页，展示所有会话卡片，使用 rough-design-skill 风格。

**相关文件：**
- 新建：`frontend/src/views/SessionHistory.tsx`

**设计规范参考：**
- 边框: `border: 3px solid #1A1A1A`
- 阴影: `box-shadow: 4px 4px 0px 0px #1A1A1A`
- Hover: `box-shadow: 8px 8px 0px 0px #1A1A1A; transform: translate(-4px, -4px)`
- 标签使用 `RoughBadge` 组件（已有）
- 返回导航使用 `PageNav` 组件（已有）
- 卡片背景色: 灌输式 `#FFF9C4`, 启发式 `#E3F2FD`, 讨论式 `#E8F5E9`
- 字体: 标题 Plus Jakarta Sans, 正文 Be Vietnam Pro

- [ ] **Step 1：创建 SessionHistory 组件**

新建 `frontend/src/views/SessionHistory.tsx`：

```tsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import RoughButton from '../components/RoughButton'
import Footer from '../components/Footer'
import { getSessionList } from '../apis/session'
import type { SessionSummary } from '../apis/session'

const TEACHING_MODE_LABELS: Record<string, string> = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
}

const MODE_BG_COLORS: Record<string, string> = {
  didactic: '#FFF9C4',
  heuristic: '#E3F2FD',
  discussion: '#E8F5E9',
}

const MODE_BADGE_VARIANT: Record<string, 'yellow' | 'blue' | 'green'> = {
  didactic: 'yellow',
  heuristic: 'blue',
  discussion: 'green',
}

const STATUS_LABELS: Record<string, string> = {
  running: '进行中',
  completed: '已完成',
  interrupted: '已中断',
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return ''
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}分钟`
  const hours = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hours}小时${remainMins}分钟`
}

function formatDate(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SessionHistory() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getSessionList()
      .then((data) => {
        if (!cancelled) setSessions(data)
      })
      .catch((err: unknown) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <Wrapper>
      <div className="bg-decoration-left" aria-hidden="true" />
      <div className="bg-decoration-right" aria-hidden="true" />

      <PageNav title="课堂历史记录" onBack={() => navigate('/')} backLabel="← 首页" />

      <main className="main">
        {loading && <div className="loading-text">加载中...</div>}
        {error && <div className="error-text">{error}</div>}

        {!loading && sessions.length === 0 && (
          <div className="empty-state">
            <div className="empty-card">
              <span className="material-symbols-outlined empty-icon">history</span>
              <p className="empty-title">还没有课堂记录</p>
              <p className="empty-desc">开始一节观察模式课程，记录将显示在这里</p>
              <RoughButton
                variant="primary"
                onClick={() => navigate('/observation/config')}
              >
                开始观察 →
              </RoughButton>
            </div>
          </div>
        )}

        {!loading && sessions.length > 0 && (
          <div className="session-grid">
            {sessions.map((session, index) => (
              <article
                key={session.id}
                className={`session-card mode-${session.teaching_mode} ${index % 2 === 0 ? 'rotate-left' : 'rotate-right'}`}
                onClick={() => navigate(`/history/${session.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') navigate(`/history/${session.id}`)
                }}
              >
                <div className="tape tape-left" aria-hidden="true" />
                <div className="card-content">
                  <div className="card-tags">
                    <RoughBadge variant={MODE_BADGE_VARIANT[session.teaching_mode] ?? 'blue'}>
                      {TEACHING_MODE_LABELS[session.teaching_mode] ?? session.teaching_mode}
                    </RoughBadge>
                    <RoughBadge
                      variant={session.status === 'completed' ? 'green' : session.status === 'running' ? 'blue' : 'yellow'}
                    >
                      {STATUS_LABELS[session.status] ?? session.status}
                    </RoughBadge>
                  </div>
                  <h2 className="card-title">{session.topic}</h2>
                  <div className="card-meta">
                    <span>{formatDate(session.start_time)}</span>
                    {session.duration_seconds !== null && (
                      <>
                        <span className="meta-divider">·</span>
                        <span>{formatDuration(session.duration_seconds)}</span>
                      </>
                    )}
                    <span className="meta-divider">·</span>
                    <span>{session.student_count} 名学生</span>
                  </div>
                  {session.checkpoint_progress && (
                    <div className="progress-section">
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{
                            width: `${session.checkpoint_progress.total > 0
                              ? (session.checkpoint_progress.completed / session.checkpoint_progress.total) * 100
                              : 0}%`,
                          }}
                        />
                      </div>
                      <span className="progress-text">
                        {session.checkpoint_progress.completed}/{session.checkpoint_progress.total} 检查点
                      </span>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </main>

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  width: 100%;
  background: #f9f9f9;
  color: #1a1c1c;
  color-scheme: light;
  display: flex;
  flex-direction: column;
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;

  /* 背景装饰 */
  .bg-decoration-left {
    position: fixed;
    top: 10%;
    left: -5%;
    width: 200px;
    height: 200px;
    background: rgba(46, 92, 255, 0.03);
    border-radius: 50%;
    filter: blur(40px);
    pointer-events: none;
    z-index: 0;
  }

  .bg-decoration-right {
    position: fixed;
    bottom: 10%;
    right: -5%;
    width: 250px;
    height: 250px;
    background: rgba(39, 224, 169, 0.03);
    border-radius: 50%;
    filter: blur(50px);
    pointer-events: none;
    z-index: 0;
  }

  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 32px 24px 64px;
    position: relative;
    z-index: 1;
  }

  .loading-text,
  .error-text {
    text-align: center;
    font-size: 18px;
    color: #525252;
    padding: 64px 0;
  }

  .error-text {
    color: #b7102a;
  }

  /* 空状态 */
  .empty-state {
    display: flex;
    justify-content: center;
    padding: 64px 0;
  }

  .empty-card {
    text-align: center;
    padding: 48px 40px;
    border: 3px dashed #d4d4d4;
    max-width: 400px;
  }

  .empty-icon {
    font-size: 64px;
    color: #d4d4d4;
    display: block;
    margin-bottom: 16px;
  }

  .empty-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    font-weight: 700;
    margin: 0 0 8px;
    color: #525252;
  }

  .empty-desc {
    font-size: 16px;
    color: #737373;
    margin: 0 0 24px;
    line-height: 1.6;
  }

  /* 会话卡片网格 */
  .session-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 32px;

    @media (min-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  /* 会话卡片 */
  .session-card {
    position: relative;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 28px;
    cursor: pointer;
    transition: transform 0.3s ease, box-shadow 0.3s ease;

    &:hover {
      box-shadow: 8px 8px 0px 0px #1a1a1a;
      transform: translate(-4px, -4px);
    }

    &:focus-visible {
      outline: 2px dashed #1a1a1a;
      outline-offset: 4px;
    }

    &.mode-didactic {
      background: #fff9c4;
    }

    &.mode-heuristic {
      background: #e3f2fd;
    }

    &.mode-discussion {
      background: #e8f5e9;
    }

    &.rotate-left {
      transform: rotate(-0.5deg);

      &:hover {
        transform: translate(-4px, -4px) rotate(-0.5deg);
      }
    }

    &.rotate-right {
      transform: rotate(0.5deg);

      &:hover {
        transform: translate(-4px, -4px) rotate(0.5deg);
      }
    }
  }

  /* 胶带 */
  .tape {
    position: absolute;
    top: -16px;
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    border-left: 1px solid rgba(200, 200, 200, 0.3);
    border-right: 1px solid rgba(200, 200, 200, 0.3);
  }

  .tape-left {
    left: -8px;
    transform: rotate(-15deg);
  }

  .card-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .card-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 24px;
    font-weight: 800;
    margin: 4px 0;
    color: #171717;
    line-height: 1.3;
  }

  .card-meta {
    font-size: 14px;
    color: #525252;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .meta-divider {
    color: #d4d4d4;
  }

  /* 进度条 */
  .progress-section {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 4px;
  }

  .progress-bar {
    flex: 1;
    height: 12px;
    border: 2px solid #1a1a1a;
    background: #fafafa;
    clip-path: polygon(0% 2%, 100% 0%, 98% 100%, 2% 98%);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: #27e0a9;
    transition: width 0.3s ease;
  }

  .progress-text {
    font-size: 13px;
    font-weight: 700;
    color: #525252;
    white-space: nowrap;
  }

  /* 响应式 */
  @media (max-width: 768px) {
    .main {
      padding: 16px 16px 48px;
    }

    .card-title {
      font-size: 20px;
    }
  }
`
```

- [ ] **Step 2：验证页面能渲染**

Run: `cd frontend && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 3：提交**

```bash
git add frontend/src/views/SessionHistory.tsx
git commit -m "feat(frontend): 新增 SessionHistory 历史记录列表页"
```

---

## 任务 5：前端 SessionDetail 详情页

目标：实现会话详情页，左侧消息时间线，右侧检查点进度面板，使用 rough-design-skill 风格。

**相关文件：**
- 新建：`frontend/src/views/SessionDetail.tsx`

**设计规范：**
- 消息按时间正序（最早在最上）
- 教师消息左边框蓝色 `#2e5cff`，学生消息左边框绿色 `#27e0a9`
- 检查点面板黄色便签 `#FFF9C4` 背景，顶部胶带装饰
- message_type 标签背景色参照设计文档映射表
- 返回按钮使用 `PageNav` 组件

- [ ] **Step 1：创建 SessionDetail 组件**

新建 `frontend/src/views/SessionDetail.tsx`：

```tsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import styled from 'styled-components'
import PageNav from '../components/PageNav'
import RoughBadge from '../components/RoughBadge'
import Footer from '../components/Footer'
import { getSessionMessages, getSessionList } from '../apis/session'
import { getCheckpointPlan } from '../apis/observation'
import type { SessionSummary, SessionMessage } from '../apis/session'
import type { CheckpointItem } from '../apis/observation'

const TEACHING_MODE_LABELS: Record<string, string> = {
  didactic: '灌输式',
  heuristic: '启发式',
  discussion: '讨论式',
}

const MODE_BADGE_VARIANT: Record<string, 'yellow' | 'blue' | 'green'> = {
  didactic: 'yellow',
  heuristic: 'blue',
  discussion: 'green',
}

const STATUS_LABELS: Record<string, string> = {
  running: '进行中',
  completed: '已完成',
  interrupted: '已中断',
}

const MESSAGE_TYPE_LABELS: Record<string, string> = {
  LECTURE: '讲授',
  CHECKPOINT_QUESTION: '提问',
  ANSWER_TO_CHECKPOINT: '回答',
  ASK_QUESTION: '主动提问',
  REPLY_TO_STUDENT: '回复',
  ASSIGN_HOMEWORK: '布置作业',
  HOMEWORK_SUBMISSION: '提交作业',
  HOMEWORK_FEEDBACK: '作业反馈',
  END_FEEDBACK: '结束反馈',
}

const MESSAGE_TAG_BG: Record<string, string> = {
  LECTURE: '#E3F2FD',
  CHECKPOINT_QUESTION: '#FFF9C4',
  ANSWER_TO_CHECKPOINT: '#E8F5E9',
  ASK_QUESTION: '#FCE4EC',
  REPLY_TO_STUDENT: '#E3F2FD',
  ASSIGN_HOMEWORK: '#fafafa',
  HOMEWORK_SUBMISSION: '#fafafa',
  HOMEWORK_FEEDBACK: '#E3F2FD',
  END_FEEDBACK: '#FFF9C4',
}

/** 已知的教师 sender 名称 */
const TEACHER_SENDERS = ['教师', 'teacher', 'Teacher']

function isTeacher(sender: string): boolean {
  return TEACHER_SENDERS.some((t) => sender.includes(t))
}

function formatTime(isoString: string | null | undefined): string {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return ''
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}分钟`
  const hours = Math.floor(mins / 60)
  const remainMins = mins % 60
  return `${hours}小时${remainMins}分钟`
}

function formatDate(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const [session, setSession] = useState<SessionSummary | null>(null)
  const [messages, setMessages] = useState<SessionMessage[]>([])
  const [checkpoints, setCheckpoints] = useState<CheckpointItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    const sid = Number(sessionId)
    let cancelled = false
    setLoading(true)

    Promise.all([
      getSessionList().then((list) => list.find((s) => s.id === sid) ?? null),
      getSessionMessages(sid),
      getCheckpointPlan(sid).catch(() => null),
    ])
      .then(([foundSession, msgs, plan]) => {
        if (cancelled) return
        setSession(foundSession)
        setMessages(msgs)
        if (plan) setCheckpoints(plan.checkpoints)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载失败')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [sessionId])

  if (loading) return <Wrapper><div className="loading-text">加载中...</div></Wrapper>
  if (error || !session) return <Wrapper><div className="error-text">{error ?? '会话不存在'}</div></Wrapper>

  return (
    <Wrapper>
      <PageNav
        title="课堂详情"
        onBack={() => navigate('/history')}
        backLabel="← 返回历史"
        right={
          <RoughBadge variant={MODE_BADGE_VARIANT[session.teaching_mode] ?? 'blue'}>
            {TEACHING_MODE_LABELS[session.teaching_mode] ?? session.teaching_mode}
          </RoughBadge>
        }
      />

      <main className="main">
        {/* 会话信息头部 */}
        <div className="session-header">
          <h1 className="session-topic">{session.topic}</h1>
          <div className="session-meta">
            <RoughBadge variant={session.status === 'completed' ? 'green' : 'yellow'}>
              {STATUS_LABELS[session.status] ?? session.status}
            </RoughBadge>
            <span className="meta-item">{formatDate(session.start_time)}</span>
            {session.duration_seconds !== null && (
              <span className="meta-item">{formatDuration(session.duration_seconds)}</span>
            )}
            <span className="meta-item">{session.student_count} 名学生</span>
          </div>
        </div>

        {/* 两栏布局 */}
        <div className="content-layout">
          {/* 左侧消息时间线 */}
          <div className="timeline-panel">
            {messages.length === 0 && (
              <div className="empty-messages">暂无消息记录</div>
            )}
            {messages.map((msg) => {
              const teacher = isTeacher(msg.sender)
              return (
                <div key={msg.id} className={`message-item ${teacher ? 'teacher' : 'student'}`}>
                  <div className="message-dot" aria-hidden="true" />
                  <div className="message-card">
                    <div className="message-header">
                      <span className="sender-name">{msg.sender}</span>
                      <span
                        className="message-type-tag"
                        style={{ background: MESSAGE_TAG_BG[msg.message_type] ?? '#fafafa' }}
                      >
                        {MESSAGE_TYPE_LABELS[msg.message_type] ?? msg.message_type}
                      </span>
                      <span className="message-time">{formatTime(msg.timestamp)}</span>
                    </div>
                    <div className="message-content">{msg.content}</div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* 右侧检查点面板 */}
          {checkpoints.length > 0 && (
            <div className="checkpoint-panel">
              <div className="tape" aria-hidden="true" />
              <h2 className="panel-title">检查点进度</h2>
              <div className="checkpoint-list">
                {checkpoints.map((cp, index) => (
                  <div key={index} className={`checkpoint-item state-${cp.state}`}>
                    <span className="checkpoint-icon" aria-hidden="true">
                      {cp.state === 'complete' ? '✓' : cp.state === 'teaching' || cp.state === 'questions' ? '●' : '○'}
                    </span>
                    <span className="checkpoint-title">{cp.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />
    </Wrapper>
  )
}

const Wrapper = styled.div`
  min-height: 100dvh;
  width: 100%;
  background: #f9f9f9;
  color: #1a1c1c;
  color-scheme: light;
  display: flex;
  flex-direction: column;
  font-family: 'Be Vietnam Pro', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  position: relative;
  overflow: hidden;

  .loading-text,
  .error-text {
    text-align: center;
    font-size: 18px;
    padding: 64px 0;
    color: #525252;
  }

  .error-text {
    color: #b7102a;
  }

  .main {
    width: 100%;
    max-width: 1152px;
    margin: 0 auto;
    padding: 24px 24px 64px;
  }

  /* 会话头部 */
  .session-header {
    margin-bottom: 32px;
  }

  .session-topic {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 12px;
    color: #171717;
  }

  .session-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .meta-item {
    font-size: 14px;
    color: #525252;
  }

  /* 两栏布局 */
  .content-layout {
    display: flex;
    flex-direction: column;
    gap: 24px;

    @media (min-width: 768px) {
      flex-direction: row;
    }
  }

  /* 消息时间线 */
  .timeline-panel {
    flex: 1;
    min-width: 0;
  }

  .empty-messages {
    text-align: center;
    color: #737373;
    padding: 48px 0;
    font-size: 16px;
  }

  .message-item {
    position: relative;
    padding-left: 32px;
    padding-bottom: 20px;

    &:last-child {
      padding-bottom: 0;
    }
  }

  .message-dot {
    position: absolute;
    left: 8px;
    top: 12px;
    width: 10px;
    height: 10px;
    border: 2px solid #1a1a1a;
    background: #fafafa;
  }

  .message-item.teacher .message-dot {
    background: #2e5cff;
  }

  .message-item.student .message-dot {
    background: #27e0a9;
    transform: rotate(45deg);
  }

  /* 时间线竖线（用左边框模拟） */
  .message-item {
    border-left: 2px dashed #d4d4d4;

    &:last-child {
      border-left-color: transparent;
    }
  }

  .message-card {
    background: #fafafa;
    border: 2px solid #1a1a1a;
    padding: 16px;
    box-shadow: 2px 2px 0px 0px #1a1a1a;
  }

  .message-item.teacher .message-card {
    border-left: 4px solid #2e5cff;
  }

  .message-item.student .message-card {
    border-left: 4px solid #27e0a9;
    transform: rotate(-0.3deg);
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }

  .sender-name {
    font-weight: 700;
    font-size: 14px;
    color: #171717;
  }

  .message-type-tag {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border: 1px solid #1a1a1a;
    color: #525252;
  }

  .message-time {
    font-size: 12px;
    color: #a3a3a3;
    margin-left: auto;
  }

  .message-content {
    font-size: 15px;
    line-height: 1.6;
    color: #404040;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* 检查点面板 */
  .checkpoint-panel {
    width: 100%;
    background: #fff9c4;
    border: 3px solid #1a1a1a;
    box-shadow: 4px 4px 0px 0px #1a1a1a;
    padding: 24px;
    position: relative;
    transform: rotate(0.5deg);

    @media (min-width: 768px) {
      width: 280px;
      min-width: 280px;
    }
  }

  .tape {
    position: absolute;
    top: -16px;
    right: -8px;
    width: 64px;
    height: 32px;
    background: rgba(227, 242, 253, 0.6);
    backdrop-filter: blur(1px);
    transform: rotate(15deg);
    border-left: 1px solid rgba(200, 200, 200, 0.3);
    border-right: 1px solid rgba(200, 200, 200, 0.3);
  }

  .panel-title {
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    font-size: 18px;
    font-weight: 800;
    margin: 0 0 16px;
    color: #171717;
  }

  .checkpoint-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .checkpoint-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    padding: 4px 0;

    &.state-complete {
      color: #006247;
    }

    &.state-teaching,
    &.state-questions {
      color: #2e5cff;
      font-weight: 700;
    }

    &.state-pending {
      color: #525252;
    }
  }

  .checkpoint-icon {
    font-size: 14px;
    width: 20px;
    text-align: center;
    flex-shrink: 0;
  }

  .checkpoint-title {
    line-height: 1.4;
  }

  /* 响应式 */
  @media (max-width: 768px) {
    .session-topic {
      font-size: 24px;
    }

    .checkpoint-panel {
      transform: none;
    }
  }
`
```

- [ ] **Step 2：验证类型检查通过**

Run: `cd frontend && npx tsc --noEmit`
Expected: 无类型错误

- [ ] **Step 3：提交**

```bash
git add frontend/src/views/SessionDetail.tsx
git commit -m "feat(frontend): 新增 SessionDetail 会话详情页"
```

---

## 任务 6：路由注册与导航按钮启用

目标：在 App.tsx 注册新路由，在 LandingPage 启用历史按钮。

**相关文件：**
- 修改：`frontend/src/App.tsx`
- 修改：`frontend/src/views/LandingPage.tsx`

- [ ] **Step 1：在 App.tsx 注册路由**

修改 `frontend/src/App.tsx`，添加导入和路由：

将文件内容替换为：

```tsx
import { Routes, Route } from 'react-router-dom'
import LandingPage from './views/LandingPage'
import ObservationConfig from './views/ObservationConfig'
import ObservationView from './views/ObservationView'
import SessionHistory from './views/SessionHistory'
import SessionDetail from './views/SessionDetail'
import NotFoundPage from './views/NotFoundPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/history" element={<SessionHistory />} />
      <Route path="/history/:sessionId" element={<SessionDetail />} />
      <Route path="/observation/config" element={<ObservationConfig />} />
      <Route path="/observation/session/:sessionId" element={<ObservationView />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
```

- [ ] **Step 2：在 LandingPage 启用历史按钮**

修改 `frontend/src/views/LandingPage.tsx` 第 23 行，将：

```tsx
<button className="nav-icon" aria-label="教学历史" disabled>
```

改为：

```tsx
<button className="nav-icon" aria-label="教学历史" onClick={() => navigate('/history')}>
```

- [ ] **Step 3：验证类型检查和 lint**

Run: `cd frontend && npx tsc --noEmit && npm run lint`
Expected: 无错误

- [ ] **Step 4：提交**

```bash
git add frontend/src/App.tsx frontend/src/views/LandingPage.tsx
git commit -m "feat(frontend): 注册历史记录路由，启用导航历史按钮"
```

---

## 自查清单

**Spec 覆盖检查：**
- [x] 会话生命周期管理（Prerequisites 中的 status/end_time/duration 更新） → 任务 1
- [x] GET /sessions/ 列表 API（LEFT JOIN、student_count、checkpoint_progress） → 任务 2
- [x] 无检查点计划时返回 null → 任务 2 测试覆盖
- [x] 按 start_time DESC 排序 → 任务 2 测试覆盖
- [x] 前端 API 层（SessionSummary、getSessionList） → 任务 3
- [x] SessionHistory 列表页（卡片网格、空状态、rough-design 风格） → 任务 4
- [x] SessionDetail 详情页（消息时间线 + 检查点面板） → 任务 5
- [x] 路由注册（/history、/history/:sessionId） → 任务 6
- [x] 导航按钮启用 → 任务 6
- [x] teaching_mode 中文映射和卡片颜色 → 任务 4
- [x] message_type 样式映射 → 任务 5
- [x] 粗边框、硬阴影、轻微旋转、胶带装饰 → 任务 4 和 5
