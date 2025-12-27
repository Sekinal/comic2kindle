# Manga to Kindle

A modern web application for converting manga files (CBR/CBZ/EPUB) to Kindle and Kobo-compatible formats with intelligent metadata handling, image optimization, and AI upscaling.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Next.js](https://img.shields.io/badge/next.js-16-black.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

---

## Features

### Core Functionality
- **Multi-format Support** - Convert CBR, CBZ, ZIP, RAR, and EPUB files
- **Output Formats** - Generate EPUB, MOBI, or both
- **Batch Processing** - Upload and convert multiple files at once
- **File Merging** - Combine multiple chapters into a single volume with auto-splitting at size thresholds

### Image Processing
- **Device Profiles** - Optimized presets for Kindle (Basic, Paperwhite 5, Scribe) and Kobo (Clara 2E, Libra 2, Sage)
- **Double-Page Spread Detection** - Automatically detects and handles wide manga pages
- **AI Upscaling** - Real-ESRGAN integration for 2x-4x image enhancement (GPU recommended)
- **Smart Resizing** - Lanczos algorithm for high-quality image scaling
- **Parallel Processing** - 6-8x faster conversion using multi-threaded image processing

### Metadata Management
- **Smart Filename Parsing** - Automatically extracts series, chapter, and volume from filenames
- **MangaDex Integration** - Search and import metadata from MangaDex
- **AniList Integration** - Alternative metadata source with cover art
- **Cover Selection** - Choose cover images from search results or extracted pages
- **Custom Metadata** - Full control over title, author, series, and description

### User Experience
- **Drag & Drop Upload** - Simple file upload with preview thumbnails
- **4-Step Wizard** - Guided workflow: Upload → Metadata → Settings → Download
- **Real-time Progress** - Live status updates during conversion
- **Dark Mode** - Eye-friendly interface (default)
- **Internationalization** - Multi-language support (English, Spanish)

---

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/manga-kindle.git
cd manga-kindle

# Start the application
docker compose up --build

# Access the web interface
open http://localhost:3000
```

### Local Development

**Prerequisites:**
- Python 3.12+
- Node.js 20+
- Calibre (for MOBI conversion)
- unrar/p7zip (for archive extraction)

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## Installation

### Docker Installation

1. **Install Docker and Docker Compose**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
   - [Docker Engine](https://docs.docker.com/engine/install/) (Linux)

2. **Clone and Start**
   ```bash
   git clone https://github.com/yourusername/manga-kindle.git
   cd manga-kindle
   docker compose up -d
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Installation

#### Backend Setup

```bash
cd backend

# Install uv (Astral's Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y calibre unrar-free p7zip-full

# Run the server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Run development server
npm run dev

# Or build for production
npm run build
npm start
```

---

## Usage Guide

### Step 1: Upload Files

1. Navigate to http://localhost:3000
2. Click **"Start Converting"** or drag files directly onto the page
3. Supported formats: `.cbr`, `.cbz`, `.zip`, `.rar`, `.epub`
4. Maximum file size: 500MB per file
5. Thumbnails will be generated automatically for preview

### Step 2: Configure Metadata

**Automatic Detection:**
- Filenames are parsed to extract series, chapter, and volume
- Example: `One Piece - Vol.01 Ch.001.cbz` → Series: "One Piece", Volume: 1, Chapter: 1

**Metadata Search:**
1. Click the search icon next to the title field
2. Search MangaDex or AniList by title
3. Select a result to auto-fill metadata and cover image

**Manual Entry:**
- Title, Author, Series name
- Chapter info (supports ranges like "Ch. 1-10")
- Volume number
- Description

### Step 3: Configure Settings

**Device Profile:**
| Profile | Resolution | Best For |
|---------|-----------|----------|
| Kindle Basic | 600×800 | Older Kindles, small file sizes |
| Kindle Paperwhite 5 | 1236×1648 | Modern Kindle e-readers |
| Kindle Scribe | 1860×2480 | Largest Kindle display |
| Kobo Clara 2E | 1072×1448 | Compact Kobo readers |
| Kobo Libra 2 | 1264×1680 | Mid-size Kobo readers |
| Kobo Sage | 1440×1920 | Premium Kobo readers |
| Custom | User-defined | Specific requirements |

**Image Options:**
- **Spread Detection** - Split double-page spreads for better viewing
- **Upscale Method** - None, Lanczos (fast), or AI/Real-ESRGAN (slow but high quality)
- **Fill Screen** - Expand images to use full device screen

**Output Options:**
- **Format** - EPUB, MOBI, or Both
- **Naming Pattern** - Template for output filenames
- **Merge Files** - Combine all uploads into one file
- **Max Output Size** - Auto-split merged files (default: 200MB)

### Step 4: Convert & Download

1. Click **"Start Conversion"**
2. Monitor progress through the status tracker:
   - Extracting → Processing → Converting → Complete
3. Download individual files or all as a ZIP archive
4. Files are available for 24 hours after conversion

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_DIR` | `.data/uploads` | File upload storage location |
| `OUTPUT_DIR` | `.data/output` | Converted file storage location |
| `PREVIEW_DIR` | `.data/previews` | Thumbnail storage location |
| `MAX_UPLOAD_SIZE` | `524288000` (500MB) | Maximum upload file size in bytes |
| `MAX_OUTPUT_FILE_SIZE` | `209715200` (200MB) | Auto-split threshold for merged files |
| `ENABLE_AI_UPSCALING` | `0` | Enable Real-ESRGAN (`1` to enable) |
| `FORCE_CPU_UPSCALING` | `0` | Force CPU mode for AI upscaling |

### Docker Compose Configuration

```yaml
services:
  backend:
    environment:
      - ENABLE_AI_UPSCALING=1        # Enable AI upscaling
      - FORCE_CPU_UPSCALING=0        # Use GPU if available
    volumes:
      - uploads:/app/uploads         # Persistent upload storage
      - output:/app/output           # Persistent output storage
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia         # GPU passthrough for AI upscaling
              count: 1
              capabilities: [gpu]
```

### Image Quality Settings

Located in `backend/app/config.py`:

```python
JPEG_QUALITY = 85           # JPEG compression quality (0-100)
MAX_IMAGE_WIDTH = 1600      # Maximum image width in pixels
MAX_IMAGE_HEIGHT = 2400     # Maximum image height in pixels
PREVIEW_WIDTH = 150         # Thumbnail width
PREVIEW_HEIGHT = 200        # Thumbnail height
```

---

## API Reference

### Upload Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload manga files, returns session ID |
| `GET` | `/api/upload/{session_id}` | List files in session |
| `PATCH` | `/api/upload/{session_id}/order` | Reorder files for merging |
| `GET` | `/api/upload/{session_id}/{file_id}/preview` | Get file thumbnail |
| `GET` | `/api/upload/{session_id}/{file_id}/parse` | Parse filename for metadata |
| `POST` | `/api/upload/{session_id}/suggest-order` | AI-suggested reading order |
| `DELETE` | `/api/upload/{session_id}` | Delete entire session |
| `DELETE` | `/api/upload/{session_id}/{file_id}` | Delete single file |

### Conversion Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/convert` | Start conversion job |
| `GET` | `/api/convert/{job_id}/status` | Get job status and progress |
| `GET` | `/api/convert` | List all jobs (filter by session_id) |

**Conversion Request Body:**
```json
{
  "session_id": "abc123",
  "file_ids": ["file1", "file2"],
  "output_format": "epub",
  "metadata": {
    "title": "One Piece Vol. 1",
    "author": "Eiichiro Oda",
    "series": "One Piece",
    "volume": 1
  },
  "device_profile": "kindle_paperwhite_5",
  "image_options": {
    "upscale_method": "lanczos",
    "detect_spreads": true,
    "fill_screen": false
  },
  "merge_files": false,
  "max_output_size_mb": 200
}
```

### Metadata Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/metadata/search` | Search MangaDex/AniList |
| `GET` | `/api/metadata/cover?url=...` | Proxy cover image download |

**Search Request Body:**
```json
{
  "query": "One Piece",
  "source": "mangadex"
}
```

### Download Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/download/{session_id}` | List available downloads |
| `GET` | `/api/download/{session_id}/{filename}` | Download single file |
| `GET` | `/api/download/{session_id}/all` | Download all files as ZIP |

### Device Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/devices` | List all device profiles |
| `GET` | `/api/devices/{profile_id}` | Get specific device specs |
| `GET` | `/api/devices/capabilities` | Get system capabilities |

### Full API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Compose                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────────────────┐ │
│  │    Frontend      │         │          Backend             │ │
│  │   (Next.js 16)   │  HTTP   │        (FastAPI)             │ │
│  │                  │◄───────►│                              │ │
│  │  - React 19      │         │  - Upload/Extract            │ │
│  │  - shadcn/ui     │         │  - Image Processing          │ │
│  │  - Zustand       │         │  - EPUB/MOBI Creation        │ │
│  │  - TailwindCSS   │         │  - Metadata Lookup           │ │
│  │                  │         │  - AI Upscaling              │ │
│  │  Port: 3000      │         │                              │ │
│  │                  │         │  Port: 8000                  │ │
│  └──────────────────┘         └──────────────────────────────┘ │
│           │                              │                      │
│           │                              │                      │
│           ▼                              ▼                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Docker Volumes                         │  │
│  │  uploads/  │  output/  │  previews/                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       External APIs           │
              │  MangaDex  │  AniList         │
              └───────────────────────────────┘
```

### Backend Services

```
backend/app/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration and settings
├── models/
│   └── schemas.py          # Pydantic models and enums
├── api/
│   ├── deps.py             # Dependency injection
│   └── routes/
│       ├── upload.py       # File upload endpoints
│       ├── convert.py      # Conversion job endpoints
│       ├── metadata.py     # Metadata search endpoints
│       ├── download.py     # File download endpoints
│       └── devices.py      # Device profile endpoints
└── services/
    ├── converter.py        # EPUB/MOBI creation (parallel processing)
    ├── extractor.py        # CBR/CBZ/EPUB extraction
    ├── image_processor.py  # Image scaling and optimization
    ├── ai_upscaler.py      # Real-ESRGAN integration
    ├── device_profiles.py  # Device specifications database
    ├── metadata_lookup.py  # MangaDex/AniList API clients
    ├── filename_parser.py  # Smart filename parsing
    ├── merger.py           # File merging with auto-split
    ├── file_manager.py     # Upload/output file management
    └── epub_reader.py      # EPUB reading utilities
```

### Frontend Components

```
frontend/src/
├── app/
│   ├── page.tsx            # Landing page
│   ├── layout.tsx          # Root layout with providers
│   └── convert/
│       └── page.tsx        # 4-step conversion wizard
├── components/
│   ├── file-dropzone.tsx   # Drag-and-drop upload
│   ├── file-list.tsx       # File preview and management
│   ├── metadata-editor.tsx # Metadata form
│   ├── metadata-search.tsx # MangaDex/AniList search
│   ├── device-selector.tsx # Device profile picker
│   ├── image-options.tsx   # Image processing settings
│   ├── conversion-settings.tsx # Output format options
│   ├── progress-tracker.tsx    # Conversion progress
│   ├── theme-toggle.tsx    # Dark/light mode
│   ├── language-selector.tsx  # i18n selector
│   └── ui/                 # shadcn/ui components
├── lib/
│   ├── api.ts              # API client functions
│   ├── store.ts            # Zustand state management
│   └── utils.ts            # Utility functions
└── types/
    └── index.ts            # TypeScript type definitions
```

### Conversion Pipeline

```
Input File (CBR/CBZ/EPUB)
         │
         ▼
┌─────────────────────┐
│    Extractor        │ ─── Extract images from archive/EPUB
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Image Processor    │ ─── Resize, upscale, detect spreads
│  (Parallel)         │     Uses ThreadPoolExecutor
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   EPUB Builder      │ ─── Create EPUB with ebooklib
│   (ebooklib)        │     Embed metadata and images
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Calibre Convert    │ ─── Convert to MOBI (optional)
│  (ebook-convert)    │
└─────────────────────┘
         │
         ▼
     Output File
```

---

## Device Profiles

### Kindle Devices

| Profile | Resolution | DPI | Notes |
|---------|-----------|-----|-------|
| **Kindle Basic** | 600×800 | 167 | Smallest files, compatible with older devices |
| **Kindle Paperwhite 5** | 1236×1648 | 300 | Recommended for most Kindle users |
| **Kindle Scribe** | 1860×2480 | 300 | Largest Kindle, best for detailed artwork |

### Kobo Devices

| Profile | Resolution | DPI | Notes |
|---------|-----------|-----|-------|
| **Kobo Clara 2E** | 1072×1448 | 300 | Compact 6" display |
| **Kobo Libra 2** | 1264×1680 | 300 | 7" display with buttons |
| **Kobo Sage** | 1440×1920 | 300 | Premium 8" display |

### Custom Profile

Select "Custom" to specify your own dimensions:
- Width and height in pixels
- DPI for print quality
- Manufacturer (affects EPUB metadata)

---

## Image Processing Options

### Upscale Methods

| Method | Speed | Quality | Best For |
|--------|-------|---------|----------|
| **None** | Instant | Original | High-resolution source files |
| **Lanczos** | Fast | Good | Most use cases, balanced quality/speed |
| **AI (Real-ESRGAN)** | Slow | Excellent | Low-resolution scans, older manga |

### Spread Detection

Automatically detects double-page spreads (pages wider than tall by >30%) and:
- Splits into two separate pages for e-readers
- Preserves reading order (right-to-left for manga)

### Fill Screen Mode

Expands images to fill the entire device screen:
- Removes letterboxing
- May crop edges of non-standard aspect ratios

---

## Troubleshooting

### Common Issues

#### "Conversion failed" Error

**Possible causes:**
1. **Corrupted archive** - Try re-downloading or extracting manually
2. **Unsupported format** - Ensure file is CBR, CBZ, ZIP, RAR, or EPUB
3. **Empty archive** - Archive contains no image files
4. **Calibre not installed** - Required for MOBI output

**Solution:**
```bash
# Check Calibre installation
which ebook-convert

# Install Calibre (Ubuntu/Debian)
sudo apt-get install calibre
```

#### AI Upscaling Not Working

**In Docker:**
AI upscaling requires GPU passthrough which may not work in all environments.

**Solution:**
1. Use Lanczos upscaling instead (fast and good quality)
2. Or enable CPU mode (slow but works everywhere):
   ```yaml
   environment:
     - ENABLE_AI_UPSCALING=1
     - FORCE_CPU_UPSCALING=1
   ```

#### Large Files Won't Upload

**Default limit:** 500MB per file

**Solution:**
Increase the limit in `backend/app/config.py`:
```python
MAX_UPLOAD_SIZE = 1073741824  # 1GB
```

#### MOBI Conversion Fails

**Cause:** Calibre's `ebook-convert` not found

**Solution:**
```bash
# Install Calibre
sudo apt-get install calibre

# Verify installation
ebook-convert --version
```

### Docker Issues

#### Container Won't Start

```bash
# View logs
docker compose logs backend
docker compose logs frontend

# Rebuild from scratch
docker compose down -v
docker compose up --build
```

#### Permission Errors

```bash
# Fix volume permissions
sudo chown -R 1000:1000 .data/
```

### Performance Tips

1. **Use Lanczos over AI upscaling** - 10-100x faster with good quality
2. **Enable parallel processing** - Default behavior, uses all CPU cores
3. **Reduce max image dimensions** - Smaller images = faster processing
4. **Use EPUB only** - Skip MOBI if not needed (saves Calibre conversion time)

---

## Development

### Project Structure

```
manga-kindle/
├── backend/                # Python FastAPI backend
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/               # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── CLAUDE.md               # Development guidelines
└── README.md               # This file
```

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest -v

# Frontend tests
cd frontend
npm run test
```

### Code Quality

```bash
# Backend linting and formatting
cd backend
uv run ruff check .
uv run ruff format .

# Frontend linting
cd frontend
npm run lint
```

### Building for Production

```bash
# Build all containers
docker compose build

# Run in production mode
docker compose -f docker-compose.yml up -d
```

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115+ | Web framework |
| Uvicorn | 0.32+ | ASGI server |
| ebooklib | 0.18 | EPUB creation |
| Pillow | 11.0+ | Image processing |
| httpx | 0.28+ | HTTP client |
| realesrgan-ncnn-py | 1.1+ | AI upscaling |
| uv | Latest | Package manager |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.1 | React framework |
| React | 19.2 | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Styling |
| shadcn/ui | Latest | Component library |
| Zustand | 5.0 | State management |
| React Query | 5.90 | Data fetching |
| next-intl | Latest | Internationalization |
| next-themes | Latest | Theme switching |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Calibre | MOBI conversion (ebook-convert) |
| unrar-free | RAR extraction |
| p7zip-full | 7z/ZIP extraction |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Follow the coding guidelines in `CLAUDE.md`
4. Write tests for new functionality
5. Run linters and tests before committing
6. Commit with conventional commit messages: `feat: add amazing feature`
7. Push and create a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [MangaDex](https://mangadex.org/) - Manga metadata and cover images
- [AniList](https://anilist.co/) - Alternative metadata source
- [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) - AI upscaling models
- [Calibre](https://calibre-ebook.com/) - MOBI conversion
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
