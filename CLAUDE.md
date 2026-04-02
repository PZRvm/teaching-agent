# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A teaching AI agent system (教学智能体) for educational scenarios with two modes:
1. **Teacher mode**: User acts as teacher controlling multiple student AI agents
2. **Student mode**: User acts as student interacting with a teacher AI agent

## Architecture

### Frontend ([frontend/](frontend/))
- React 19 + TypeScript + Vite
- Styled-components for styling
- React Compiler enabled (via `@rolldown/plugin-babel`)

### Backend ([backend/](backend/))
- FastAPI web framework
- LangChain ecosystem for AI/agent orchestration
- ChromaDB for vector storage (RAG, knowledge base)
- SQLAlchemy + Alembic for database migrations
- OpenAI SDK for LLM integration

### Key Directories
- `backend/agents/` - AI agent implementations (teacher, student agents)
- `backend/core/` - Core business logic and services
- `backend/dependencies/` - Dependency injection setup
- `backend/middlewares/` - Custom FastAPI middleware
- `backend/routers/` - API route definitions
- `backend/configs/` - YAML configuration files (llm.yml, app.yml, database.yml, chroma.yml)
- `frontend/src/apis/` - API client functions
- `frontend/src/components/` - React components

## Development Commands

### Frontend
```bash
cd frontend
npm run dev      # Start dev server (http://localhost:5173)
npm run build    # Build for production
npm run lint     # Run ESLint
npm run preview  # Preview production build
```

### Backend
```bash
cd backend
python main.py       # Start dev server (http://0.0.0.0:8000)
ruff check .         # Check code issues
ruff check . --fix   # Auto-fix issues
ruff format .        # Format code
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Linting
- Frontend: `npm run lint` in [frontend/](frontend/)
- Backend: `ruff check .` in [backend/](backend/)
- ESLint config: [frontend/eslint.config.js](frontend/eslint.config.js)
- Ruff config: [backend/pyproject.toml](backend/pyproject.toml)
- TypeScript strict mode enabled with no-unused-locals and no-unused-parameters

## Environment

- Backend runs on port 8000 (uvicorn)
- Frontend dev server runs on port 5173 (Vite default)
- Python 3.12+ required

## Configuration

Backend uses YAML configuration files in `backend/configs/`:

- `llm.yml` - LLM settings (model, API URL, temperature)
- `app.yml` - Application settings (host, port, CORS)
- `database.yml` - Database connection settings
- `chroma.yml` - Vector database settings

Sensitive data (API keys) goes in `backend/.env` (use `.env.example` as template).

Access config in code:
```python
from configs.config import settings

# LLM config
api_key = settings.llm_api_key
model = settings.llm_model

# App config
host = settings.app_host
port = settings.app_port
```

## Code Style Guide

### Frontend Components

All React components must follow this pattern:

```tsx
import styled from 'styled-components'

export default function MyComponent() {
  return (
    <Wrapper>
      <div className="header">标题</div>
      <div className="content">
        <p className="text">内容</p>
      </div>
    </Wrapper>
  )
}

// Only ONE Wrapper styled component
// Use nested class selectors for internal elements
const Wrapper = styled.div`
  padding: 20px;

  .header {
    font-size: 24px;
  }

  .content {
    padding: 10px;

    .text {
      font-size: 16px;
    }
  }
`
```

**Rules:**
- Use only ONE `Wrapper` styled component per file
- Internal elements use regular HTML with `className` (kebab-case)
- Define nested class styles inside `Wrapper`
- Support multi-level nesting with `&`

**Naming:**
- Component files: PascalCase (`UserProfile.tsx`)
- Wrapper: Always named `Wrapper`
- Classes: kebab-case (`header`, `content`, `user-name`)

### Python Code Style

Follow PEP 8 with these additional rules:

```python
# File: backend/routers/users.py

from fastapi import APIRouter
from typing import List

router = APIRouter()


@router.get("/users/", summary="获取用户列表")
async def read_users() -> List[dict]:
    """
    获取所有用户列表

    Returns:
        List[dict]: 用户列表
    """
    return [{"username": "Rick"}, {"username": "Morty"}]
```

**Rules:**
- Use type hints for all function parameters and returns
- Add docstrings for all functions and classes
- Use `async def` for async operations
- Order imports: stdlib → third-party → local
- Max line length: 100 characters

**Naming:**
- Files and modules: `snake_case`
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`

## gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Available gstack skills:
`/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/design-consultation`, `/design-shotgun`, `/design-html`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/browse`, `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`, `/setup-deploy`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`, `/autoplan`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`

If gstack skills aren't working, run `cd .claude/skills/gstack && ./setup` to build the binary and register skills.
