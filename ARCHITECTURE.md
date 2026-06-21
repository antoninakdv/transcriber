# Architecture Overview

This document provides a comprehensive view of the Whisper Transcriber's architecture, design decisions, and data flow. It serves as both technical documentation and an interview talking point for the AI Deployment Strategist role.

## Executive Summary

The Whisper Transcriber is a **local-first, client-server application** that combines Whisper's offline speech-to-text with Mistral's optional cloud-based refinement. It's designed to be:

- **Zero-infrastructure**: No Docker, containers, databases, or external services required
- **Local-first**: All core functionality works without internet connectivity
- **Opt-in enhancement**: Mistral refinement is a progressive enhancement, not a requirement
- **Data-control oriented**: Users explicitly choose when/if data leaves their machine
- **Extensible**: Registry pattern allows easy addition of new refinement modes

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                              USER                                        │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           BROWSER (Frontend)                              │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  React 19 + Vite                                                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐     │  │
│  │  │  App     │  │ HomePage │  │ FileList │  │Transcription │     │  │
│  │  │          │  │          │  │          │  │    View      │     │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐│  │
│  │  │                    API Client (axios)                          ││  │
│  │  │  GET /api/files          - List/manage files                   ││  │
│  │  │  POST /api/transcribe    - Start transcription job              ││  │
│  │  │  GET /api/transcribe/{job_id}/status - Job status              ││  │
│  │  │  GET /api/transcribe/{file_id}/result - Get transcript         ││  │
│  │  │  POST /api/export/docx/{file_id} - Export to DOCX            ││  │
│  │  │  GET /api/refine/modes   - List refinement modes               ││  │
│  │  │  GET /api/refine/available - Check Mistral availability         ││  │
│  │  │  POST /api/refine/{file_id} - Refine transcript                ││  │
│  │  └─────────────────────────────────────────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                     │ HTTP/JSON (localhost:8000)
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND (FastAPI)                                │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  main.py: FastAPI app with CORS, routes, middleware                 │  │
│  │  config.py: Configuration constants and paths                      │  │
│  │  models.py: Pydantic models for request/response                   │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         ROUTERS                                      │  │
│  │  files.py:      File upload, listing, deletion, audio serving       │  │
│  │  transcribe.py: Transcription job management                        │  │
│  │  export.py:     DOCX export functionality                           │  │
│  │  refine.py:     Mistral refinement endpoints                        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                         SERVICES                                     │  │
│  │  file_service.py:   File I/O, metadata, storage                    │  │
│  │  whisper_service.py: Whisper model loading, transcription          │  │
│  │  docx_service.py:   DOCX generation with python-docx                 │  │
│  │  settings_service.py: Settings management, no direct mutation      │  │
│  │  mistral_client.py: Mistral API client, error handling             │  │
│  │  refine.py:        Refinement service, mode registry, prompts       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                     │
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Whisper Models     │    │   workspace/         │    │   Mistral API        │
│   (downloaded locally)│    │   uploads/          │    │   (cloud, optional)   │
│                      │    │   recordings/       │    │                      │
│  - tiny.en (39M)     │    │   exports/          │    │  - mistral-tiny      │
│  - base.en (74M)     │    │   *.meta.json       │    │  - mistral-small     │
│  - small.en (244M)   │    │   *.transcription   │    │  - mistral-large     │
│  - medium.en (769M)  │    │   *.json           │    │                      │
│  - large (1550M)     │    └─────────────────────┘    └─────────────────────┘
└─────────────────────┘
```

## Design Principles

### 1. Local-First Architecture
- **Core functionality** works without internet connectivity
- **Whisper transcription** happens entirely locally
- **Mistral refinement** is opt-in and cloud-based
- **Data sovereignty** maintained by default

### 2. Separation of Concerns
- **Routers**: HTTP endpoints and request handling
- **Services**: Business logic and data processing
- **Models**: Data structures and validation
- **Clients**: External service communication

### 3. Progressive Enhancement
- **Base experience**: Full functionality without Mistral
- **Enhanced experience**: Better results with Mistral API key
- **Graceful degradation**: Missing API key disables refinement cleanly

### 4. Data Control by Design
- **Explicit user choice**: Refined text only sent to Mistral when user clicks "Refine"
- **No automatic calls**: Whisper-only is first-class mode
- **No data persistence**: Transcripts never leave local storage without user action
- **Secure key handling**: Environment variables, never hardcoded

## Data Flow

### Basic Transcription Flow
```
User Action → File Upload → Save to workspace → Return FileInfo
                           ↓
                    User Clicks "Transcribe"
                           ↓
              Create Job (pending) → Add to jobs dict
                           ↓
              Background Thread: Load Whisper Model → Transcribe Audio
                           ↓
              Save Transcription → Update Job (completed) → Notify Frontend
                           ↓
              Frontend Polls Status → Displays Results
```

### Refinement Flow
```
User Selects Mode → Clicks "Refine Transcript"
                           ↓
              Frontend calls /api/refine/{file_id}
                           ↓
              Backend: Get Transcription Text → Check API Key → Call Mistral
                           ↓
              Mistral: System Prompt + User Prompt (transcript) → Generate Refined Text
                           ↓
              Backend: Format Response → Return RefinementResult
                           ↓
              Frontend: Display Refined Text → Enable Toggle → Update Export
```

### Export Flow
```
User Clicks "Export DOCX"
                           ↓
              Backend: Get Transcription + File Info → Generate DOCX
                           ↓
              python-docx: Create Document → Add Metadata → Add Content
                           ↓
              Return FileResponse → Browser Download
```

## Component Details

### Backend Components

#### main.py - Application Entry
- FastAPI application with CORS middleware
- Settings endpoints (GET/PUT /api/settings)
- Health check endpoint (GET /api/health)
- Route inclusion for all routers
- Application state management

#### config.py - Configuration
- Directory paths (BASE_DIR, WORKSPACE_DIR, UPLOADS_DIR, etc.)
- Allowed file extensions
- Whisper model list and default model
- Settings file path

#### models.py - Data Models
- FileInfo: File metadata
- TranscriptionSegment: Timestamp + text
- TranscriptionResult: Full transcription with segments
- JobStatus: Job tracking state
- Settings: Application settings

#### Services Layer

**file_service.py**
- `save_upload()`: Save uploaded files with metadata
- `save_recording()`: Save recorded audio
- `list_files()`: Get all uploaded/recorded files
- `get_file_path()`: Get path for a file ID
- `save_transcription()`: Save transcription results
- `get_transcription()`: Retrieve transcription by file ID
- `delete_file()`: Remove files and metadata

**whisper_service.py**
- `_get_whisper()`: Lazy import of whisper module
- `load_model()`: Load and cache Whisper models
- `transcribe()`: Run transcription on audio file

**docx_service.py**
- `format_timestamp()`: Convert seconds to HH:MM:SS
- `generate_docx()`: Create DOCX from transcription result
- Supports both original and refined text export

**settings_service.py**
- `get_settings()`: Load settings from file or defaults
- `set_settings()`: Save settings to file and update cache
- `get_default_model()`: Get current default model

**mistral_client.py**
- `MistralClientService`: Main client class
- `refine_text()`: Call Mistral chat API with prompts
- Custom exception hierarchy (AuthenticationError, RateLimitError, NetworkError)
- Singleton pattern via `get_mistral_client()`

**refine.py**
- `RefinementMode`: Enum of 5 modes
- `RefinementResult`: Result data structure
- `RefinementModeConfig`: Mode configuration
- `RefinementService`: Main service with registry
- `PROMPT_TEMPLATES`: All mode prompts with version comments
- `get_refinement_service()`: Singleton access

#### Routers Layer

**files.py**
- POST /api/files/upload: Upload file
- POST /api/files/recording: Save recording
- GET /api/files: List all files
- GET /api/files/{file_id}/audio: Serve audio file
- DELETE /api/files/{file_id}: Delete file

**transcribe.py**
- POST /api/transcribe/{file_id}: Start transcription job
- GET /api/transcribe/{job_id}/status: Get job status
- GET /api/transcribe/{file_id}/result: Get transcription result
- Uses ThreadPoolExecutor for non-blocking transcription
- Job state management with cleanup

**export.py**
- POST /api/export/docx/{file_id}: Export transcription to DOCX
- POST /api/export/docx/refined/{file_id}: Export refined transcription
- Returns FileResponse with proper Content-Disposition

**refine.py**
- GET /api/refine/modes: List available refinement modes
- GET /api/refine/available: Check if Mistral is configured
- POST /api/refine/{file_id}: Refine existing transcription
- POST /api/refine/text: Refine arbitrary text

### Frontend Components

#### App Structure
- **App.jsx**: Main application with state management
- **HomePage.jsx**: Main page with FileDropZone and FileList
- **SettingsPanel.jsx**: Settings sidebar

#### Components
- **FileDropZone.jsx**: Drag/drop, paste, file browser upload
- **AudioRecorder.jsx**: In-browser recording with hooks
- **FileList.jsx**: Table of files with actions
- **TranscriptionView.jsx**: Display transcription with refinement
- **RefinementPanel.jsx**: Mistral refinement UI
- **Navbar.jsx**: Navigation bar
- **ProgressBar.jsx**: Job progress display
- **ModelSelector.jsx**: Model selection dropdown

#### Hooks
- **useTranscription.js**: Manage transcription state and polling
- **useRefinement.js**: Manage refinement modes and API calls
- **useAudioRecorder.js**: Audio recording functionality

#### API Client (client.js)
- Axios-based HTTP client
- All API endpoint methods
- Proper error handling

## Refinement Mode Registry Pattern

```
PROMPT_TEMPLATES = {
    "meeting_notes": RefinementModeConfig(
        name="Meeting Notes",
        description="Structured summary...",
        system_prompt="You are a professional meeting...",
        user_prompt_template="Here is the meeting transcript:...",
        model="mistral-small-latest",
        temperature=0.3,
        output_format="text"
    ),
    "clean_transcript": RefinementModeConfig(
        name="Clean Transcript",
        description="Rewrite transcript naturally...",
        system_prompt="You are a transcription refinement...",
        user_prompt_template="Please clean up this transcript:...",
        model="mistral-small-latest",
        temperature=0.1,  # Low for fidelity
        output_format="text"
    ),
    # ... 3 more modes
}

Service.get_available_modes() → Returns mode info for UI
Service.refine(transcript, mode_id) → Calls appropriate prompt
```

**Benefits:**
- Zero changes needed to add new modes
- Single source of truth for mode configurations
- Consistent error handling across all modes
- Easy to test and maintain

## Error Handling Strategy

### Backend Errors
```python
class MistralClientError(Exception):        # Base class
    pass

class MistralAuthenticationError(MistralClientError):
    pass  # No API key configured

class MistralRateLimitError(MistralClientError):
    pass  # Rate limit exceeded

class MistralNetworkError(MistralClientError):
    pass  # Network issues
```

### Frontend Error States
- **API unavailable**: Show user-friendly message about missing API key
- **Network errors**: Display retry option
- **Rate limits**: Show helpful message with cooldown info
- **Validation errors**: Clear messages about what's wrong

### Graceful Degradation
- Mistral refinement disabled when no API key
- Whisper-only mode fully functional
- All UI elements present but disabled when unavailable

## Security Measures

### API Key Handling
1. **Primary**: Environment variable (`.env` file, git-ignored)
2. **Secondary**: Session-only UI input (masked password field)
3. **Optional**: OS keychain for persistence (not implemented yet)

**Never:**
- Hardcoded in source code
- Committed to git
- Logged or echoed to console
- Transmitted anywhere except Mistral API

### Data Protection
- All audio files stored locally
- All transcriptions stored locally
- Mistral API only called when user explicitly requests refinement
- No telemetry or usage tracking
- Proper CORS configuration (localhost only by default)

## Performance Considerations

### Whisper Model Caching
- Models downloaded once and cached on disk
- In-memory cache prevents repeated loading
- Automatic cache cleanup when memory pressure high

### Job Management
- ThreadPoolExecutor with max_workers=1 (prevents resource exhaustion)
- Job cleanup removes completed/failed jobs from memory
- Non-blocking HTTP responses with background processing

### Frontend Optimization
- React hooks for efficient state management
- Proper cleanup of intervals and event listeners
- Lazy loading of heavy components

## Configuration Management

### Settings Flow
```
Settings.json file ←→ settings_service.py ←→ API endpoints ←→ React state
```

- Single source of truth (settings.json)
- No direct config module mutation
- Settings cached in memory for performance
- Changes immediately reflected in API

### Environment Variables
- `MISTRAL_API_KEY`: Primary API key source
- Future: Configurable backend/fronted ports

## Deployment Considerations

### Single-Command Startup
```batch
@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

start "Whisper Backend" /MIN cmd /c "cd /d %SCRIPT_DIR%backend && venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000"

start "Whisper Frontend" /MIN cmd /c "cd /d %SCRIPT_DIR%frontend && npx vite --host"

timeout /t 5 >nul
start "" "http://localhost:5173"
```

**Key features:**
- Relative paths (portable across machines)
- Minimized windows (`/MIN` flag)
- Auto-open browser
- Proper timeout for server startup

### Cross-Platform Support
- **Windows**: Uses `.bat` files, works with venv
- **macOS/Linux**: Similar approach with shell scripts
- **Dependency**: Only Python and Node.js required

## Dependencies

### Backend (requirements.txt)
```
fastapi==0.115.12        # Web framework
uvicorn==0.34.3          # ASGI server
openai-whisper           # Local transcription
python-docx              # DOCX generation
python-multipart          # File upload handling
pydantic>=2.0            # Data validation
mistralai>=2.0           # Mistral API client (only new dependency)
```

### Frontend (package.json)
```json
{
  "react": "^19.2.6",
  "react-dom": "^19.2.6", 
  "react-router-dom": "^7.15.1",
  "axios": "^1.16.1",
  "vite": "^8.0.12"
}
```

**Constraint**: Only `mistralai` added as new dependency per requirements.

## Data Storage

### File System Structure
```
backend/
├── workspace/
│   ├── uploads/
│   │   ├── {file_id}.{ext}           # Audio files
│   │   ├── {file_id}.meta.json       # File metadata
│   │   └── {file_id}.transcription.json  # Transcription results
│   ├── recordings/
│   │   ├── {file_id}.webm           # Recorded audio
│   │   ├── {file_id}.meta.json      # Recording metadata
│   │   └── {file_id}.transcription.json # Transcription results
│   └── exports/
│       └── {filename}_transcription.docx  # Exported documents
│       └── {filename}_{mode}_refined.docx  # Refined exports
├── settings.json          # Application settings
└── .env                  # Environment variables (git-ignored)
```

### No Database
- File-based storage for simplicity
- No additional infrastructure required
- Easy to backup and migrate
- Scales to hundreds of files

## Interview Talking Points

### Why This Architecture Works for AI Deployment Strategist

#### 1. **Pragmatic LLM Integration**
- Not just a demo, but a **production-ready** implementation
- Real workflow: voice → text → LLM → document
- Solves actual user problems (cleanup, summarization, action items)

#### 2. **Enterprise-Grade Considerations**
- **Data control**: Maps directly to Mistral's enterprise proposition
- **Cost awareness**: Low temperature for fidelity, configurable models
- **Error handling**: Comprehensive classification and user messaging
- **Security**: Proper key management, no secrets in code

#### 3. **Architectural Excellence**
- **Local-first**: Respects data sovereignty requirements
- **Opt-in enhancement**: Progressive enhancement done right
- **Separation of concerns**: Clean layer boundaries
- **Extensibility**: Registry pattern for easy extension

#### 4. **Deployment Strategy**
- **Zero infrastructure**: No barriers to adoption
- **Single command**: Simple for end users
- **Cross-platform**: Works everywhere
- **User-friendly**: Non-technical users can operate

#### 5. **Code Quality**
- **Readable by non-engineers**: As required
- **Type hints throughout**: Better IDE support, fewer bugs
- **Small functions**: Single responsibility, easy to understand
- **Proper documentation**: Docstrings, comments where needed

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Two-process architecture | Separation of concerns, easier development |
| FastAPI backend | Modern, async, great docs, Python ecosystem |
| React frontend | Industry standard, great developer experience |
| Local-first design | Privacy, offline capability, data control |
| Registry pattern for modes | Easy extension, single source of truth |
| Environment variables for keys | Security, portability, best practice |
| ThreadPoolExecutor for jobs | Non-blocking, resource management |

### Trade-offs Made

| Trade-off | Choice | Reasoning |
|-----------|--------|-----------|
| Frontend framework | React vs Vue/Svelte | Familiarity, ecosystem, existing code |
| Backend framework | FastAPI vs Flask/Django | Modern async, type hints, OpenAPI |
| Model caching | In-memory vs disk | Performance vs complexity |
| API calls | Direct vs queue | Simplicity vs reliability |
| Error handling | Custom vs built-in | Better user experience, specific messages |

## Future Enhancements

### Short Term
- Session-only API key input in UI (masked)
- OS keychain integration for key persistence
- Chunking for long transcripts (context window)
- Concurrent transcription support

### Medium Term
- Audio playback during recording
- File size limits and validation
- Rate limiting for API calls
- Better progress reporting

### Long Term
- Multiple language support
- Speaker diarization
- Custom model support
- Batch processing

## Summary

This architecture demonstrates a **pragmatic, production-ready approach** to LLM integration that:

1. **Solves real problems** with clear value
2. **Respects user privacy** with local-first design
3. **Provides opt-in enhancement** without locking users in
4. **Is easy to deploy** with zero infrastructure
5. **Is easy to extend** with clean patterns
6. **Is explainable** line-by-line to non-engineers

It's the **AI Deployment Strategist role in miniature** - exactly the kind of solution that would be proposed for enterprise customers who need LLM capabilities without complexity or compromise on data control.