# Manga to Kindle - Development Guidelines

## Project Overview

A web application for converting manga (CBR/CBZ) to Kindle-compatible formats (EPUB/MOBI) with proper metadata handling.

## Tech Stack

- **Frontend**: Next.js 15 + shadcn/ui + Tailwind CSS
- **Backend**: Python 3.12 + FastAPI
- **Package Manager**: astral's `uv` (for Python), npm/pnpm (for Node)
- **Conversion Engine**: Calibre CLI (ebook-convert)
- **Containerization**: Docker + Docker Compose

---

## Coding Practices

### TypeScript (Frontend)
- Enable strict mode in tsconfig.json
- Use explicit types, avoid `any`
- Prefer interfaces over type aliases for object shapes
- Use `const` by default, `let` only when mutation is needed
- Handle all Promise rejections

### Python (Backend)
- Use type hints everywhere (parameters, returns, variables)
- Follow PEP 8 style guidelines
- Use `ruff` for linting and formatting
- Write docstrings for public functions and classes
- Use `Pydantic` models for request/response validation

### General
- Handle errors explicitly - no silent failures
- Log errors with context (file, line, relevant data)
- Keep functions small and focused (< 50 lines)
- Use meaningful variable and function names
- Write self-documenting code; add comments only for non-obvious logic

---

## UI/UX Guidelines

### Design System
- Use **shadcn/ui** components consistently
- **Dark theme** as default (manga-reading friendly)
- Follow Tailwind best practices (utility-first, avoid arbitrary values)
- Use CSS variables for theming

### Accessibility
- Add ARIA labels to interactive elements
- Ensure keyboard navigation works
- Maintain sufficient color contrast
- Support screen readers

### Layout
- Responsive design (mobile-first approach)
- Wizard-style flow: Upload → Rename → Metadata → Convert → Download
- Clear visual hierarchy
- Prominent progress indicators

### Interactions
- Drag & drop for file uploads
- Batch operations with "apply to all" patterns
- Inline previews of covers and pages
- Clear error messages with recovery suggestions

---

## Git Practices

### Commits
- Commit frequently with descriptive messages
- Use **conventional commits** format:
  - `feat:` new feature
  - `fix:` bug fix
  - `chore:` maintenance tasks
  - `docs:` documentation updates
  - `refactor:` code refactoring
  - `test:` adding/updating tests
  - `style:` formatting changes

### Branch Strategy
- `main` - production-ready code
- `develop` - integration branch
- `feat/*` - feature branches
- `fix/*` - bug fix branches

### Safety
- Never commit secrets or `.env` files
- Run tests before committing
- Review diffs before committing
- Keep commits atomic (one logical change per commit)

---

## Docker Guidelines

### Dockerfiles
- Use multi-stage builds for smaller images
- Don't run as root in containers (use non-root user)
- Pin dependency versions explicitly
- Use `.dockerignore` to exclude unnecessary files

### Docker Compose
- Use named volumes for persistent data
- Define health checks for services
- Use environment variables for configuration
- Document port mappings

---

## Testing Requirements

### Backend (Python)
- Write unit tests for all services
- Integration tests for API endpoints
- Use `pytest` with fixtures
- Aim for >80% coverage on critical paths
- Test error cases, not just happy paths

### Frontend (TypeScript)
- Component tests with React Testing Library
- Integration tests for user flows
- Mock API calls in tests
- Test accessibility

### Before Committing
1. Run linters (`ruff`, `eslint`)
2. Run formatters (`ruff format`, `prettier`)
3. Run all tests
4. Verify Docker builds successfully

---

## MCP Tools

### context7
- **Always use context7 MCP** for documentation lookup
- Query context7 before implementing unfamiliar APIs
- Use it to verify best practices for libraries

### Usage Examples
```
# Before implementing MangaDex API
context7: How to use MangaDex API v5?

# Before using ebooklib
context7: Python ebooklib EPUB creation examples

# Before using Calibre CLI
context7: Calibre ebook-convert command options
```

---

## Project Commands

### Development
```bash
# Start all services
docker compose up

# Start with rebuild
docker compose up --build

# Backend only
docker compose up backend

# Frontend only
docker compose up frontend
```

### Backend
```bash
cd backend
uv sync                    # Install dependencies
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run uvicorn app.main:app --reload  # Dev server
```

### Frontend
```bash
cd frontend
npm install               # Install dependencies
npm run dev               # Dev server
npm run build             # Production build
npm run lint              # Lint
npm run test              # Run tests
```

---

## File Structure Reference

```
manga-kindle/
├── CLAUDE.md              # This file
├── docker-compose.yml
├── .gitignore
├── README.md
│
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities
│   │   └── types/         # TypeScript types
│   └── ...
│
└── backend/
    ├── app/
    │   ├── api/routes/    # FastAPI endpoints
    │   ├── services/      # Business logic
    │   ├── models/        # Pydantic schemas
    │   └── utils/         # Helpers
    └── tests/             # Pytest tests
```
