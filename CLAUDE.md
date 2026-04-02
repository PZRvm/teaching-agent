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
python main.py   # Start dev server (http://0.0.0.0:8000)
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Linting
- Frontend: `npm run lint` in [frontend/](frontend/)
- ESLint config: [frontend/eslint.config.js](frontend/eslint.config.js)
- TypeScript strict mode enabled with no-unused-locals and no-unused-parameters

## Environment

- Backend runs on port 8000 (uvicorn)
- Frontend dev server runs on port 5173 (Vite default)
- Python 3.12+ required

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

## gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

Available gstack skills:
`/office-hours`, `/plan-ceo-review`, `/plan-eng-review`, `/plan-design-review`, `/design-consultation`, `/design-shotgun`, `/design-html`, `/review`, `/ship`, `/land-and-deploy`, `/canary`, `/benchmark`, `/browse`, `/connect-chrome`, `/qa`, `/qa-only`, `/design-review`, `/setup-browser-cookies`, `/setup-deploy`, `/retro`, `/investigate`, `/document-release`, `/codex`, `/cso`, `/autoplan`, `/careful`, `/freeze`, `/guard`, `/unfreeze`, `/gstack-upgrade`, `/learn`

If gstack skills aren't working, run `cd .claude/skills/gstack && ./setup` to build the binary and register skills.
