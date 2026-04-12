"""Session 模型包.

目录结构：
- router.py / router_websocket.py — 路由层（HTTP + WebSocket 端点）
- services/ — 服务层（业务逻辑）
  - observation_service.py — SessionOrchestrator（观察模式核心）
  - teacher_service.py — TeacherSessionController（教师模式核心）
  - websocket_handlers.py — WebSocket 命令处理器
- schemas.py — 数据模型
"""
