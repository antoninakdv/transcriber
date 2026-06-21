# Architecture

A short tour of how the Transcriber is put together and how data flows through it.

## Overview

The app is two processes:

- **Backend** — FastAPI (Python) served by Uvicorn. Handles uploads/recordings, runs transcription (local Whisper or cloud Voxtral), stores transcripts, exports `.docx`, and proxies refinement calls to Mistral.
- **Frontend** — React 19 (Vite) single-page app that talks to the backend over a small REST API.

Both run on localhost. Audio and transcripts live on disk under `backend/workspace/`; nothing is sent anywhere unless you choose the Voxtral engine or run a refinement.

```
Browser (React) ──HTTP──> FastAPI ──> services ──> { Whisper (local) | Mistral API (cloud) }
                                   └─> workspace/ (audio, transcripts, exports)
```

Dependencies flow one way: **routers → services → clients**. Prompt templates and config are data, kept out of the logic.

## Backend

### Routers (`backend/routers/`)
- `files.py` — upload, save recording, list, serve audio (HTTP range supported), delete.
- `transcribe.py` — start a transcription job, poll status, get/update the transcript.
- `export.py` — generate a `.docx` for the original/edited or a refined transcript.
- `refine.py` — list modes, report availability, run a refinement.

### Services (`backend/services/`)
- `transcription_engines.py` — a small `TranscriptionEngine` interface with two implementations: `WhisperEngine` (local, default) and `VoxtralEngine` (Mistral cloud). Both return the same normalized result (`text`, `language`, `segments`, `model`), so everything downstream is engine-agnostic. Adding an engine is one new class.
- `whisper_service.py` — loads and caches the Whisper model and runs transcription.
- `mistral_client.py` — single source of truth for the Mistral API key (resolution: env/`.env` → session → OS keychain) and all Mistral calls: chat (refinement), Voxtral speech-to-text, and a lightweight connection test. Typed errors for auth/rate-limit/network.
- `refine.py` — the refinement mode registry. Each mode is one entry holding a system prompt, user-prompt template, model, and temperature.
- `file_service.py` — stores audio, metadata, and transcripts; enforces allowed types and a size limit; writes files under a generated id (never the client filename).
- `docx_service.py` — builds the Word document.
- `settings_service.py` — loads/saves `settings.json` (Whisper model + engine).

### Models (`backend/models.py`)
Pydantic models for files, transcription segments/results (including the recorded `engine` and an `edited` flag), job status, and settings.

## Frontend

- `api/client.js` — all backend calls in one place.
- `hooks/` — `useTranscription` (start + poll a job, resilient to transient status-poll failures), `useRefinement`, `useAudioRecorder`.
- `components/` — `FileList`, `TranscriptionView` (segments, per-segment playback, edit/save, refinement panel, export), `RefinementPanel`, `AudioRecorder`, `FileDropZone`, etc.
- `pages/` — `HomePage` (upload/record + file list + active-engine banner), `SettingsPanel` (model, engine, API key).

## Key data flows

**Transcription.** The frontend uploads audio, then starts a job. The backend resolves the engine from saved settings, runs the engine in a background thread (so CPU-bound Whisper never blocks the event loop), records the engine and model on the transcript, and saves it. The frontend polls job status and shows the result.

**Editing.** Saving an edited transcript `PUT`s the new text; it becomes the canonical text (segments are kept as a timing reference) and is what export and refinement use.

**Refinement.** A chosen mode loads the transcript's text, builds a system/user prompt from the registry, calls Mistral, and returns the refined artifact. The raw transcript is never overwritten.

**Playback.** Each segment carries numeric start/end seconds; the transcript view uses one shared `<audio>` element to seek to a segment's start, play, and auto-pause at its end.

## API-key handling

The key is resolved by `mistral_client.get_active_key()` in this order:

1. `MISTRAL_API_KEY` environment variable / `.env` (primary)
2. A key entered this session via Settings (in memory only)
3. A key the user chose to remember (OS keychain via `keyring`)

The raw key is never written to `settings.json` or any plaintext file, never logged, and never returned to the browser — the API exposes only whether a key is set, its source, and a last-4 hint.

## Data storage

```
backend/workspace/
├── uploads/      {id}.{ext}, {id}.meta.json, {id}.transcription.json
├── recordings/   {id}.{ext}, {id}.meta.json, {id}.transcription.json
└── exports/      {name}_transcription.docx, {name}_{mode}_refined.docx
```

All of `workspace/` is git-ignored. `settings.json` holds non-secret defaults (model, engine).

## Security posture

- Backend binds to `127.0.0.1`; CORS is restricted to the local frontend origins.
- Upload type and size are validated server-side; files are written under a generated id, so a client filename can't influence the path on disk.
- External calls use the Mistral SDK over HTTPS with timeouts; audio, transcript content, and the API key are never logged.

## Dependencies

- **Backend**: FastAPI, Uvicorn, `openai-whisper`, `python-docx`, `python-multipart`, `pydantic`, `mistralai`, `keyring`.
- **Frontend**: React, React DOM, Axios; Vite + ESLint for tooling.
