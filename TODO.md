# Manga to Kindle - Development Progress

## Project Location
`/home/ieqr/Desktop/manga-kindle`

---

## Completed Files

### Root Level
```
/home/ieqr/Desktop/manga-kindle/
├── CLAUDE.md              ✅ Coding guidelines, context7 MCP, best practices
├── docker-compose.yml     ✅ Frontend + backend services, shared volumes
├── .gitignore             ✅ Python, Node, Docker, IDE files
└── TODO.md                ✅ This file
```

### Backend (`/home/ieqr/Desktop/manga-kindle/backend/`)
```
backend/
├── Dockerfile             ✅ Python 3.12 + Calibre + unrar-free + p7zip
├── pyproject.toml         ✅ uv dependencies (fastapi, ebooklib, pillow, httpx, etc.)
├── uv.lock                ✅ Lock file generated
│
└── app/
    ├── __init__.py        ✅
    ├── config.py          ✅ Settings with env var support
    ├── main.py            ✅ FastAPI app, CORS, health check, router mounts
    │
    ├── api/
    │   ├── __init__.py    ✅
    │   ├── deps.py        ✅ Dependency injection for services
    │   └── routes/
    │       ├── __init__.py ✅
    │       ├── upload.py   ✅ POST /upload, GET/DELETE /upload/{session_id}
    │       ├── metadata.py ✅ POST /metadata/search, GET /metadata/cover
    │       ├── convert.py  ✅ POST /convert, GET /convert/{job_id}/status
    │       └── download.py ✅ GET /download/{session_id}/{filename}, GET /download/{session_id}/all
    │
    ├── models/
    │   ├── __init__.py    ✅
    │   └── schemas.py     ✅ FileInfo, MangaMetadata, ConversionJob, etc.
    │
    └── services/
        ├── __init__.py        ✅
        ├── file_manager.py    ✅ Session/file management
        ├── extractor.py       ✅ CBR/CBZ extraction (zip, unrar, 7z)
        ├── converter.py       ✅ EPUB/MOBI generation with ebooklib + Calibre
        └── metadata_lookup.py ✅ MangaDex + AniList API integration
```

### Frontend (`/home/ieqr/Desktop/manga-kindle/frontend/`)
```
frontend/
├── Dockerfile             ✅ Multi-stage Node 20 Alpine build
├── package.json           ✅ Next.js 15 + shadcn/ui + dependencies
├── next.config.ts         ✅ Standalone output for Docker
├── components.json        ✅ shadcn/ui configuration
│
└── src/
    ├── app/
    │   ├── layout.tsx     ✅ ThemeProvider, Toaster, dark mode
    │   ├── page.tsx       ✅ Landing page with hero and features
    │   ├── globals.css    ✅ Tailwind v4 + CSS variables
    │   └── convert/
    │       └── page.tsx   ✅ Main wizard: Upload → Metadata → Settings → Download
    │
    ├── components/
    │   ├── file-dropzone.tsx      ✅ Drag & drop with react-dropzone
    │   ├── file-list.tsx          ✅ Table with checkboxes, file info
    │   ├── metadata-editor.tsx    ✅ Form with cover preview
    │   ├── metadata-search.tsx    ✅ Dialog for MangaDex/AniList search
    │   ├── conversion-settings.tsx ✅ Format selection, naming pattern
    │   ├── progress-tracker.tsx   ✅ Real-time progress, download links
    │   ├── theme-provider.tsx     ✅ next-themes wrapper
    │   └── ui/                    ✅ shadcn/ui components
    │
    ├── lib/
    │   ├── api.ts         ✅ Typed API client
    │   ├── store.ts       ✅ Zustand state management
    │   └── utils.ts       ✅ shadcn utilities (cn)
    │
    └── types/
        └── index.ts       ✅ TypeScript interfaces matching backend
```

---

## What Needs To Be Done

### 1. Backend Tests (MEDIUM PRIORITY)

```
backend/tests/
├── __init__.py
├── conftest.py         # Fixtures: temp dirs, sample CBZ files
├── test_extractor.py   # Test ZIP/RAR extraction, image sorting
├── test_converter.py   # Test EPUB creation, metadata embedding
└── test_api.py         # Integration tests for all endpoints
```

### 2. Final Steps

- [ ] Test Docker Compose build: `docker compose up --build`
- [ ] Test full workflow manually with real CBZ files
- [ ] Create `README.md` with setup instructions
- [ ] Initial git commit

---

## Important Notes

### Calibre CLI Warning
User reported Calibre CLI can be buggy. The `converter.py` has fallback logic:
- Always creates EPUB first (pure Python, reliable)
- MOBI conversion is optional and catches errors gracefully
- Modern Kindles (2022+) support EPUB natively, so MOBI is less critical

### context7 MCP
Plugin is installed. Use it to look up:
- MangaDex API v5 documentation
- ebooklib EPUB creation
- Calibre ebook-convert options
- shadcn/ui component usage

### Ports
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

---

## Quick Commands

```bash
# Backend dev server
cd /home/ieqr/Desktop/manga-kindle/backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev server
cd /home/ieqr/Desktop/manga-kindle/frontend
npm run dev

# Docker (full stack)
cd /home/ieqr/Desktop/manga-kindle
docker compose up --build

# Run backend tests
cd /home/ieqr/Desktop/manga-kindle/backend
uv run pytest -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 User Browser                            │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Frontend (Next.js :3000)                   │
│  - File upload UI (react-dropzone)                      │
│  - Batch rename interface                               │
│  - Metadata search (MangaDex/AniList)                   │
│  - Conversion progress tracking                         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP API
┌────────────────────────▼────────────────────────────────┐
│              Backend (FastAPI :8000)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ FileManager │ │ Extractor   │ │ Converter   │       │
│  │ (sessions)  │ │ (CBR→imgs)  │ │ (imgs→EPUB) │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│  ┌─────────────────────────────────────────────┐       │
│  │ MetadataLookup (MangaDex + AniList APIs)    │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```
