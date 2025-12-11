# ✨ Fairy Story Generator

An AI-powered web app that creates personalized, kid-safe fairy tales. The backend (FastAPI) generates text with Gemini, images with Vertex AI Imagen, and voiceovers with gTTS, storing everything in Supabase. The frontend (Next.js) shows live progress and lets kids read and listen scene by scene.

## What this project does
- **Story writing**: Gemini 2.5 Flash Lite with prompts tuned for ages 4–10.
- **Illustrations**: 16:9 images via Vertex AI Imagen; graceful placeholder on failure.
- **Narration**: gTTS (auto EN/VI detection) using a thread pool to avoid blocking.
- **Fast delivery**: Scene 1 is returned immediately; remaining scenes are generated in background batches with progress tracking.
- **Storage**: Supabase PostgreSQL + Storage; public URLs for image/audio.
- **Live updates**: Progress polling endpoint so the UI can update every 2 seconds.

## High-level architecture
```
Next.js (frontend)
    ↕ REST /api/v1/stories/*
FastAPI (backend)
    ↳ Gemini (story text)
    ↳ Vertex AI (images)
    ↳ gTTS (voice)
    ↳ Supabase (DB + Storage)
```
Flow: `POST /stories/generate` → save story + return scene 1 → background worker builds remaining scenes in parallel batches → frontend polls `/stories/{id}/progress` → full viewer at `/story/{id}` (images + audio controls).

## Project structure
```
backend/
  story_generator/
    main.py                      # FastAPI app, middleware, routers
    api/routes/{health,stories}.py
    models/story.py              # Pydantic schemas & enums
    services/
      story_generator.py         # Gemini client + prompt/validation
      image_generator.py         # Vertex AI + fallback placeholder
      voice_generator.py         # gTTS with thread pool
    prompts/story_prompts.py     # Prompt builder & validation
    workers/{scene_worker,task_manager}.py # Background batches
    utils/{metrics,timing,storage}.py
    config.py, database.py       # Settings + Supabase client

frontend/
  src/app/
    page.tsx                     # Landing
    create/page.tsx              # Create story + progress UI
    story/[id]/page.tsx          # Full story viewer
  src/components/*               # ProgressBar, ScenePlaceholder, etc.
  src/hooks/*                    # useStoryGeneration, useStoryPolling
  src/lib/api.ts                 # Fetch helpers
  src/types/story.ts             # TS types
```

## Setup & run
**Requirements**: Python 3.11–3.14 + Poetry, Node 18+, Supabase, Google Cloud (Vertex AI) with service-account JSON.

Backend:
```bash
cd backend
poetry install
poetry run uvicorn story_generator.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

URLs (dev): frontend http://localhost:3000 — backend http://localhost:8000 — docs http://localhost:8000/docs (only in development).

## Environment variables
`backend/.env` (essentials):
```
SUPABASE_URL=...
SUPABASE_KEY=...
GEMINI_API_KEY=...
GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=story_generator/story-generator-xxxx.json
ENVIRONMENT=development
LOG_LEVEL=DEBUG
IMAGE_STYLE=Pixar 3D style, bright lighting, colorful, high quality
TTS_VOICE=auto
```

`frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Key APIs (backend)
- `GET /health`, `GET /health/db` — service & DB checks
- `POST /api/v1/stories/generate` — create story, return scene 1 + progress info
- `GET /api/v1/stories/{id}/progress` — progress + completed scenes
- `GET /api/v1/stories/{id}` — full story (all scenes)
- `GET /api/v1/stories?limit=10` — list stories for default user

## Frontend experience
- `/` landing → CTA to `/create`.
- `/create`: form (name/prompt/theme/length/tone/style/voice), shows scene 1 immediately, progress bar, placeholders, polls every 2s.
- `/story/{id}`: full reader with image, audio play/pause, next/prev, auto-advance when audio ends.

## Troubleshooting (quick)
- Supabase: verify `SUPABASE_URL`/`SUPABASE_KEY`, buckets `story-images` and `story-audio` exist.
- Vertex AI: check credentials path, project/location, and permissions.
- CORS: update `allow_origins` in `main.py` to match your frontend URL.
- Missing media: see `services/image_generator.py` / `voice_generator.py`; placeholder is used if image fails.

## License
MIT License
