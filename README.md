# ✨ Fairy Story Generator

A web application that generates personalized AI-powered fairy tales for children, with automatic illustration generation and voice narration.

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Application](#-running-the-application)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)

## ✨ Features

- 📖 **AI Story Generation**: Uses Google Gemini 2.0 Flash to generate personalized fairy tales
- 🎨 **Illustration Generation**: Automatically generates beautiful images for each scene using Vertex AI (FLUX model)
- 🔊 **Voice Narration**: Natural text-to-speech using Microsoft Edge TTS
- 💾 **Data Storage**: Supabase for storing stories and metadata
- 🚀 **Fast Performance**: Parallel generation, takes only about 12-18 seconds per story
- 💯 **100% Free**: All APIs used are on free tier
- 🎭 **Multiple Themes**: Supports various themes like princess, dragon, forest, ocean, space, and more
- 📏 **Customizable Length**: Short (6 scenes), Medium (10 scenes), Long (14 scenes)
- 🎨 **Diverse Tones**: Funny, Adventurous, Gentle

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Python**: 3.11+
- **AI Services**:
  - Google Gemini  Flash (Story generation)
  - Google Vertex AI / FLUX (Image generation)
  - Microsoft Edge TTS (Voice synthesis)
- **Database**: Supabase (PostgreSQL)
- **Package Manager**: Poetry

### Frontend
- **Framework**: Next.js 16
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Icons**: Lucide React
- **HTTP Client**: Axios

## 🏗️ System Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──────> │   Backend    │ ──────> │  Supabase   │
│  (Next.js)  │         │   (FastAPI)  │         │  (Database) │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ├──> Google Gemini (Story)
                              ├──> Vertex AI (Images)
                              └──> Edge TTS (Voice)
```

### Story Generation Process

1. **Receive Request**: Frontend sends prompt and options (length, tone, theme, child's name)
2. **Generate Content**: Backend uses Gemini to create story plot and scenes
3. **Parallel Generation**: 
   - Generate images for each scene (parallel)
   - Generate audio for each scene (parallel)
4. **Storage**: Save all data to Supabase
5. **Return**: Return story ID and URL to view the story

## 📦 Installation

### System Requirements

- Python 3.11 or higher (< 3.15)
- Node.js 18+ and npm/yarn
- Poetry (for Python package management)
- Google Cloud account (for Vertex AI)
- Supabase account

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Install Poetry** (if not already installed):
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -
```

3. **Install dependencies**:
```bash
poetry install
```

4. **Activate virtual environment**:
```bash
poetry shell
```

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# Google Cloud / Vertex AI
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001

# Story Generation
DEFAULT_STORY_LENGTH=short
DEFAULT_NUM_SCENES=6
MAX_SCENES=12

# Image Generation
IMAGE_PROVIDER=vertex_ai
IMAGE_STYLE=Pixar 3D style, bright lighting, colorful, high quality
ENABLE_IMAGE_FALLBACK=true
MAX_IMAGE_RETRIES=3
MAX_UPLOAD_RETRIES=3

# Voice Settings
TTS_VOICE=en-US-JennyNeural
TTS_RATE=+0%
TTS_VOLUME=+0%
```

### Frontend Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Google Cloud Setup

1. Create a project on Google Cloud Console
2. Enable Vertex AI API
3. Create a service account and download credentials JSON
4. Place the credentials file in `backend/` or `backend/story_generator/` directory

### Supabase Setup

1. Create a new project on [Supabase](https://supabase.com)
2. Get URL and anon key from Settings > API
3. Create `stories` table with appropriate schema (see `backend/story_generator/database.py`)

## 🚀 Running the Application

### Development Mode

**Terminal 1 - Backend**:
```bash
cd backend
poetry shell
uvicorn story_generator.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

The application will run at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production Build

**Backend**:
```bash
cd backend
poetry install --no-dev
uvicorn story_generator.main:app --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run build
npm start
```

## 📚 API Documentation

### Endpoints

#### `POST /api/v1/stories/generate`
Generate a new story with images and audio.

**Request Body**:
```json
{
  "prompt": "A story about a brave knight",
  "story_length": "short",
  "story_tone": "adventurous",
  "theme": "dragon",
  "child_name": "Lily"
}
```

**Response**:
```json
{
  "id": "story-uuid",
  "title": "The Brave Knight",
  "status": "completed",
  "scenes": [...],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### `GET /api/v1/stories/{id}`
Get detailed information about a specific story.

#### `GET /api/v1/stories/`
Get a list of stories (with pagination).

#### `GET /health`
Health check endpoint.

View detailed documentation at: http://localhost:8000/docs (when running in development mode)

## 📁 Project Structure

```
story_gen_app/
├── backend/
│   ├── story_generator/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py      # Health check endpoints
│   │   │       └── stories.py     # Story generation endpoints
│   │   ├── models/
│   │   │   └── story.py           # Pydantic models
│   │   ├── services/
│   │   │   ├── story_generator.py # Gemini integration
│   │   │   ├── image_generator.py # Vertex AI image generation
│   │   │   └── voice_generator.py # Edge TTS integration
│   │   ├── prompts/
│   │   │   └── story_prompts.py   # AI prompts
│   │   ├── utils/
│   │   │   ├── storage.py         # Supabase storage helpers
│   │   │   └── timing.py          # Performance utilities
│   │   ├── config.py              # Settings management
│   │   ├── database.py            # Supabase client
│   │   └── main.py                # FastAPI app
│   ├── pyproject.toml             # Poetry dependencies
│   └── README.md
│
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx            # Home page
    │   │   ├── create/
    │   │   │   └── page.tsx        # Story creation page
    │   │   └── story/
    │   │       └── [id]/
    │   │           └── page.tsx    # Story viewer page
    │   ├── components/             # React components
    │   ├── lib/
    │   │   └── api.ts              # API client
    │   └── types/
    │       └── story.ts            # TypeScript types
    ├── package.json
    └── README.md
```

## 🎯 Usage

1. Open your browser and navigate to http://localhost:3000
2. Enter the child's name (optional) and click "Start Creating Magic"
3. Enter a prompt describing the story you want to create
4. Select length, tone, and theme
5. Click "Generate Story" and wait approximately 12-18 seconds
6. View the story with images and listen to audio narration

## 🔧 Troubleshooting

### Database Connection Error
- Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
- Ensure Supabase project is active

### Google Cloud Credentials Error
- Check if the credentials JSON file exists
- Ensure service account has Vertex AI User permissions
- Check `GOOGLE_APPLICATION_CREDENTIALS` path

### CORS Error
- Check if `allow_origins` in `main.py` includes the frontend URL

### Image Generation Error
- Check if Vertex AI API is enabled
- Check quota and billing of Google Cloud project

## 📝 License

MIT License

## 👤 Author

Trinh Quoc Trung

---

**Note**: Make sure you have configured all API keys and credentials correctly before running the application. All services used have free tiers, but require proper registration and configuration.
