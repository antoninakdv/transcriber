# M0 Review: Whisper Transcriber Codebase Analysis

## Executive Summary

This is a lightweight, local audio transcription tool that uses Whisper to convert audio/video files into text, with export to .docx format. The application follows a client-server architecture with a FastAPI backend and React frontend, communicating via REST API.

## What the Tool Does

The Whisper Transcriber provides:
- **Audio Upload**: Drag-and-drop, file browser selection, or paste (Ctrl+V) for audio/video files
- **Audio Recording**: In-browser audio recording with save functionality  
- **Transcription**: Whisper-based speech-to-text with configurable model selection
- **Export**: Download transcriptions as formatted .docx files
- **File Management**: List, play, view, delete uploaded/recorded files
- **Settings**: Configure Whisper model (tiny, base, small, medium, large)

## Technology Stack

### Backend
- **Framework**: FastAPI (Python) with Uvicorn server
- **Transcription**: OpenAI Whisper (local, downloaded on first use)
- **Document Generation**: python-docx library
- **Dependencies**: fastapi, uvicorn, openai-whisper, python-docx, python-multipart, pydantic
- **Architecture**: REST API with router-based organization

### Frontend
- **Framework**: React 19 with Vite build system
- **State Management**: React hooks (useState, useEffect, useCallback, useRef)
- **HTTP Client**: Axios
- **Styling**: Custom CSS (no framework)
- **Routing**: React Router DOM (present but appears unused in current flow)
- **Audio**: Web Audio API via custom hooks

### Run Architecture
- **Two-process**: Separate backend (port 8000) and frontend (port 5173) processes
- **Launcher**: Windows batch file (`start.bat`) that starts both processes and opens browser
- **Communication**: CORS-enabled API calls from frontend to backend

## File Structure Analysis

```
backend/
├── main.py           # FastAPI app entry, settings endpoints
├── config.py         # Configuration constants and paths
├── models.py         # Pydantic models for data structures
├── requirements.txt   # Python dependencies
├── services/
│   ├── __init__.py
│   ├── file_service.py    # File upload, storage, metadata
│   ├── whisper_service.py # Whisper model loading and transcription
│   └── docx_service.py    # DOCX generation
└── routers/
    ├── __init__.py
    ├── files.py       # File upload, listing, deletion, audio serving
    ├── transcribe.py  # Transcription job management
    └── export.py      # DOCX export endpoints

frontend/
├── src/
│   ├── main.jsx      # React entry point
│   ├── App.jsx       # Main app component with settings panel
│   ├── api/
│   │   └── client.js  # Axios-based API client
│   ├── pages/
│   │   ├── HomePage.jsx    # Main page with file list and controls
│   │   ├── SettingsPage.jsx # Settings interface
│   │   └── SettingsPanel.jsx # Settings sidebar
│   ├── components/
│   │   ├── FileDropZone.jsx  # Drag-drop upload component
│   │   ├── FileList.jsx      # File table with actions
│   │   ├── AudioRecorder.jsx # Recording component
│   │   ├── TranscriptionView.jsx # Transcript display
│   │   ├── Navbar.jsx        # Navigation bar
│   │   ├── ProgressBar.jsx    # Job progress indicator
│   │   └── ModelSelector.jsx  # Model selection dropdown
│   └── hooks/
│       ├── useTranscription.js  # Transcription state management
│       └── useAudioRecorder.js  # Audio recording logic
```

## Current User-Facing Features (Checklist)

### ✅ Core Functionality
- [x] **Drag and drop audio files** - Supported formats: .ogg, .mp3, .wav, .mp4, .m4a, .webm, .flac, .aac
- [x] **File browser upload** - Via hidden file input, supports multiple files
- [x] **Paste audio files** - Clipboard event listener for paste (Ctrl+V)
- [x] **Audio recording** - In-browser recording with start/stop, save functionality
- [x] **Whisper transcription** - Configurable model (tiny, base, small, medium, large)
- [x] **Transcription progress** - Status tracking with progress bar
- [x] **Audio playback** - Play uploaded/recorded audio directly in browser
- [x] **View transcription** - Display transcription with timestamps and full text

### ✅ File Management
- [x] **List all files** - Table showing name, type, size, transcription status
- [x] **Delete files** - Remove files with confirmation
- [x] **File status badges** - Visual indicators for transcription status

### ✅ Export
- [x] **DOCX export** - Download transcription as formatted Word document
- [x] **Proper filename** - Uses original filename for export

### ✅ Settings
- [x] **Model selection** - Choose from 5 Whisper models
- [x] **Save settings** - Persists model preference to settings.json
- [x] **Settings panel** - Slide-out sidebar for configuration

### ✅ UI/UX
- [x] **Responsive layout** - Main content and settings panel
- [x] **Loading states** - Visual feedback during operations
- [x] **Error handling** - User-friendly error messages
- [x] **Progress indication** - For transcription jobs

## Code Quality Assessment

### Strengths ✅
1. **Clear separation of concerns** - Router pattern separates API endpoints from business logic
2. **Service layer abstraction** - File operations, transcription, and export are well-separated
3. **Type hints** - Good use of Pydantic models and type annotations
4. **Error handling** - Consistent HTTPException usage in backend
5. **Async/await** - Proper use of async patterns throughout
6. **Concurrency** - ThreadPoolExecutor for non-blocking transcription
7. **Component structure** - React components are well-organized and reusable
8. **Custom hooks** - Good abstraction of transcription and recording logic

### Issues and Technical Debt 🔧

#### Backend Issues
1. **Global state in routers/transcribe.py**
   - `jobs` dictionary is module-level global state
   - `executor` is module-level global
   - **Risk**: Memory leaks, state persistence across requests
   - **Plumbing fix**: Move to application state or use FastAPI's dependency injection

2. **Model caching issue in whisper_service.py**
   - `_model_cache.clear()` is called on every new model load (line 17)
   - This clears ALL cached models, not just when switching
   - **Risk**: Unnecessary model reloading, performance impact
   - **Plumbing fix**: Only clear cache when memory pressure requires it

3. **Direct config mutation**
   - `config.DEFAULT_MODEL = settings.model` (main.py:48) mutates imported module
   - **Risk**: Unpredictable behavior, violates immutability
   - **Plumbing fix**: Use proper configuration management

4. **Settings persistence inconsistency**
   - Settings saved to JSON but also mutable in config module
   - **Risk**: Source of truth ambiguity
   - **Plumbing fix**: Single source of truth for settings

5. **No input validation**
   - File size limits not enforced
   - Concurrent transcription limits not implemented
   - **Risk**: Resource exhaustion, poor user experience
   - **Plumbing fix**: Add validation and limits

6. **Hardcoded paths**
   - CORS origins hardcoded in main.py:14-15
   - **Risk**: Not configurable for different environments
   - **Plumbing fix**: Make configurable

7. **No cleanup of job state**
   - Completed/failed jobs remain in memory forever
   - **Risk**: Memory leak
   - **Plumbing fix**: Implement job cleanup

#### Frontend Issues
1. **Duplicate formatTimestamp function**
   - `formatTs` in TranscriptionView.jsx (lines 1-7)
   - `format_timestamp` in docx_service.py (lines 10-16)
   - **Risk**: Code duplication, potential divergence
   - **Plumbing fix**: Shared utility function

2. **Missing error boundaries**
   - No React error boundaries for component errors
   - **Risk**: Entire app crashes on component error
   - **Plumbing fix**: Add error boundaries

3. **Hardcoded API base URL**
   - `http://localhost:8000/api` in client.js:4
   - **Risk**: Not configurable for different environments
   - **Plumbing fix**: Environment variable configuration

4. **Memory leak potential**
   - Interval not always cleaned up in useTranscription.js
   - Event listeners not cleaned up in FileDropZone.jsx
   - **Risk**: Memory leaks in long-running sessions
   - **Plumbing fix**: Proper cleanup in useEffect return functions

5. **No loading states for exports**
   - Export button has no loading indicator
   - **Risk**: User confusion during large exports
   - **Plumbing fix**: Add loading state

6. **Duplicate accepted formats definition**
   - Backend: `ALLOWED_EXTENSIONS` in config.py:12
   - Frontend: `ACCEPTED_EXTS` in FileDropZone.jsx:10
   - **Risk**: Inconsistency between frontend and backend
   - **Plumbing fix**: Single source of truth

#### Architecture Issues
1. **Hardcoded paths in start.bat**
   - References `C:\Whisper\backend` and `C:\Whisper\frontend` (lines 5,7)
   - **Risk**: Won't work from different directory, not portable
   - **Plumbing fix**: Use relative paths or current directory

2. **Two visible terminal windows**
   - `start.bat` opens two separate cmd windows (lines 5,7)
   - **Risk**: Poor user experience, cluttered desktop
   - **Plumbing fix**: Start processes minimized or in background

3. **No process management**
   - No way to stop processes cleanly
   - No process health monitoring
   - **Risk**: Orphaned processes, unclear state

## Dead Code and Unused Files ⚰️

### Backend
- **models.py**: `JobStatus` model has `file_id` field but it's not used in the job tracking
- **services/__init__.py**: Empty files (could be removed)
- **routers/__init__.py**: Empty files (could be removed)

### Frontend  
- **react-router-dom**: Imported in package.json but not used in current app flow
- **SettingsPage.jsx**: Appears to be a standalone page but only SettingsPanel.jsx is used
- **ModelSelector.jsx**: Could be more reusable

## Security Assessment 🔒

### Current State ✅
- `.gitignore` properly excludes secrets, audio files, models
- No hardcoded API keys
- Environment-based configuration possible

### Missing Security Measures ⚠️
- **No API authentication** - All endpoints accessible without auth
- **No rate limiting** - Could be abused for transcription requests
- **No file size limits** - Could upload very large files
- **No CORS configuration** - Hardcoded localhost only (actually a strength for local tool)

## Plumbing Improvements (Zero Behavior Change)

### High Priority
1. **Fix model caching** - Remove unnecessary cache clearing in whisper_service.py:17
2. **Remove global state** - Move jobs and executor to proper application state
3. **Fix settings management** - Single source of truth, no direct module mutation
4. **Add job cleanup** - Remove completed/failed jobs from memory
5. **Fix start.bat paths** - Use relative paths, auto-open browser quietly

### Medium Priority  
6. **Shared constants** - Consolidate allowed extensions, API URLs
7. **Shared utilities** - Consolidate timestamp formatting
8. **Input validation** - Add file size and concurrency limits
9. **Error boundaries** - Add React error boundaries
10. **Memory leak fixes** - Proper cleanup of intervals and event listeners

### Low Priority
11. **Configuration improvements** - Make CORS origins configurable
12. **Process management** - Better startup/shutdown experience
13. **Code organization** - Remove empty __init__.py files if unused

## Mistral Integration Planning

### Current State Assessment
- ✅ FastAPI backend ready for new endpoints
- ✅ React frontend ready for new UI components
- ✅ Service layer pattern established
- ✅ Type hints throughout (good foundation)
- ⚠️ Need to add `mistralai` dependency (already present in venv!)

### Integration Points
1. **New router**: `routers/refine.py` for Mistral refinement endpoints
2. **New service**: `services/mistral_client.py` for API calls
3. **New service**: `services/refine.py` for mode registry and prompt templates
4. **Frontend**: New components for refinement UI
5. **Configuration**: Environment variable for API key

## Environment Setup Notes

- Backend uses venv in `backend/venv/`
- Mistral SDK already installed (`mistralai-2.4.13`)
- Frontend uses npm/yarn with Vite
- Python dependencies: FastAPI, Whisper, docx, etc.

## File Checklist for M0 Completion

- [x] Read all backend files (main.py, config.py, models.py, requirements.txt)
- [x] Read all service files (file_service.py, whisper_service.py, docx_service.py)  
- [x] Read all router files (files.py, transcribe.py, export.py)
- [x] Read all frontend files (App.jsx, HomePage.jsx, components, hooks, api)
- [x] Analyze architecture and technology stack
- [x] Identify all user-facing features
- [x] Document code quality issues and technical debt
- [x] List plumbing improvements with zero behavior change
- [x] Document dead code and duplication
- [x] Create comprehensive feature checklist

---

*M0 Review completed. Ready for M1 Plumbing Refactor.*