# Whisper Transcriber with Mistral Refinement

A lightweight, local audio transcription tool that uses Whisper for speech-to-text, with optional Mistral-powered refinement for enhanced results.

## The Problem

Voice-to-text transcription is essential for meetings, interviews, and content creation, but existing solutions often have trade-offs:
- **Cloud services** require internet connectivity and may have privacy concerns
- **Local solutions** like Whisper provide privacy but can have rough output with fillers, repetitions, and errors
- **Manual cleanup** is time-consuming and doesn't scale

## The Solution

This tool provides the best of both worlds:
1. **Fully local Whisper transcription** - No internet required, complete privacy
2. **Optional Mistral refinement** - Post-process transcripts for professional results
3. **Multiple refinement modes** - Tailored processing for different use cases
4. **Zero infrastructure complexity** - Runs on your local machine with a simple startup

## Features

### Core Transcription
- ✅ **Drag and drop** audio files (OGG, MP3, WAV, MP4, M4A, WEBM, FLAC, AAC)
- ✅ **File browser upload** with multi-file support
- ✅ **Paste from clipboard** (Ctrl+V) for audio files
- ✅ **In-browser recording** with save functionality
- ✅ **Multiple Whisper models** (tiny, base, small, medium, large)
- ✅ **Progress tracking** with status indicators
- ✅ **Audio playback** directly in the browser

### File Management
- ✅ **List all files** with metadata
- ✅ **View transcriptions** with timestamps
- ✅ **Delete files** with confirmation
- ✅ **Export to DOCX** with formatting

### Mistral Refinement (Optional)
- ✅ **Meeting Notes** - Structured summary with key points and decisions
- ✅ **Clean Transcript** - Natural speech rewrite, removing fillers and repetitions
- ✅ **Action Items** - Structured checklist with tasks, owners, due dates
- ✅ **Prompt Generator** - Create best-practice LLM prompts from spoken intent
- ✅ **Custom Instruction** - Apply your own processing rules
- ✅ **Graceful degradation** - Works without API key, all features opt-in

### Data Control & Privacy
- ✅ **Whisper-only is first-class** - Full functionality without Mistral
- ✅ **Local-first design** - No data leaves your machine unless you choose
- ✅ **Secure key handling** - Environment variables, never committed
- ✅ **No tracking or telemetry**

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- pip and npm/yarn

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Transcriber
```

2. **Set up backend**
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

3. **Set up frontend**
```bash
cd frontend
npm install
cd ..
```

4. **(Optional) Set Mistral API key**
```bash
# Create .env file in project root
 echo MISTRAL_API_KEY=your_api_key_here > .env
```
Get your API key from [Mistral Console](https://console.mistral.ai/)

### Running the Application

**Simple startup (recommended):**
```bash
# On Windows:
start.bat

# On macOS/Linux:
# See Alternative Startup below
```

The application will:
- Start the backend server (port 8000) in the background
- Start the frontend server (port 5173) in the background  
- Automatically open your browser to http://localhost:5173

**Alternative startup (manual):**
```bash
# Terminal 1: Start backend
cd backend
venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev

# Then open http://localhost:5173 in your browser
```

## Usage Guide

### Basic Transcription
1. **Upload**: Drag & drop audio files, use file browser, or paste (Ctrl+V)
2. **Record**: Click "Record Audio" button, speak, then save
3. **Transcribe**: Click "Transcribe" button for any uploaded file
4. **View**: Click on transcribed files to see results
5. **Export**: Click "Export DOCX" to download formatted Word documents

### Using Mistral Refinement
1. **Transcribe** your audio file as normal
2. **View** the transcription
3. **Select refinement mode** from the "Refine with Mistral" dropdown
4. **Click "Refine Transcript"** to process
5. **Toggle** between original and refined versions
6. **Export refined** DOCX with improvements

#### Refinement Modes
| Mode | Best For | Output |
|------|----------|--------|
| **Meeting Notes** | Meetings, interviews | Structured bullet points |
| **Clean Transcript** | Presentations, speeches | Natural reading text |
| **Action Items** | Task extraction | Structured JSON/Checklist |
| **Prompt Generator** | LLM prompt creation | Best-practice prompts |
| **Custom** | Custom processing | Depends on instruction |

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python) with Uvicorn server
- **Transcription**: OpenAI Whisper (local inference)
- **Refinement**: Mistral AI API (optional, cloud-based)
- **Frontend**: React 19 with Vite build system
- **Document Export**: python-docx library

### Design Principles
- **Local-first**: All core functionality works without internet
- **Opt-in enhancement**: Mistral features are optional add-ons
- **Data control**: You control when/if data leaves your machine
- **Zero complexity**: No Docker, containers, or infrastructure required
- **Single command startup**: Everything starts with one file

### File Structure
```
backend/
├── main.py              # FastAPI application entry
├── config.py            # Configuration constants
├── models.py            # Pydantic data models
├── services/
│   ├── file_service.py  # File management
│   ├── whisper_service.py # Whisper transcription
│   ├── docx_service.py  # DOCX export
│   ├── mistral_client.py # Mistral API client
│   ├── refine.py        # Refinement service with modes
│   └── settings_service.py # Settings management
└── routers/
    ├── files.py         # File upload/listing endpoints
    ├── transcribe.py    # Transcription job endpoints
    ├── export.py        # DOCX export endpoints
    └── refine.py        # Refinement endpoints

frontend/
├── src/
│   ├── App.jsx          # Main application
│   ├── api/client.js    # API client methods
│   ├── hooks/
│   │   ├── useTranscription.js # Transcription state
│   │   └── useRefinement.js   # Refinement state
│   ├── components/
│   │   ├── TranscriptionView.jsx # Transcript display
│   │   ├── RefinementPanel.jsx # Refinement UI
│   │   └── ...          # Other components
│   └── pages/
│       └── HomePage.jsx # Main page
└── package.json
```

## Configuration

### Environment Variables
```bash
# Mistral API Key (optional)
MISTRAL_API_KEY=your_api_key_here
```

### Settings
- **Whisper Model**: Change in Settings panel (tiny, base, small, medium, large)
- Larger models provide better accuracy but use more memory and are slower

### Whisper Models Comparison
| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39M | ⚡⚡⚡⚡ | Basic | Quick testing |
| base | 74M | ⚡⚡⚡ | Good | General use |
| small | 244M | ⚡⚡ | Better | Better quality |
| medium | 769M | ⚡ | High | Professional use |
| large | 1550M | ⚡ | Best | Maximum accuracy |

## Security & Privacy

### Data Handling
- ✅ **Audio files**: Stored locally, never transmitted anywhere
- ✅ **Transcriptions**: Stored locally, never transmitted anywhere
- ✅ **API keys**: Never stored in code, never committed to git
- ✅ **Mistral API**: Only called when you explicitly choose refinement
- ✅ **No telemetry**: No usage tracking or data collection

### Key Management
API keys are handled with priority:
1. **Environment variable** (`.env` file, git-ignored)
2. **Session input** (masked, in-memory only)
3. **Optional OS keychain** (for remembering across sessions)

**Never**: Hardcoded in source, logged, or committed.

## Interview Talking Points

This project demonstrates key capabilities for an **AI Deployment Strategist** role:

### 1. **Real-World LLM Integration**
- Practical use case: voice → text → LLM refinement → document
- Clear value proposition: saves time, improves quality, maintains privacy
- Production-ready implementation with proper error handling

### 2. **Prompt Engineering Excellence**
- Evidence-based practices: system/user separation, explicit instructions
- Few-shot examples for format-sensitive tasks
- Explicit output contracts (JSON schema for action items)
- Guardrails against fabrication
- Versioned and documented prompts

### 3. **Architecture & Design**
- **Local-first**: Respects data sovereignty requirements
- **Opt-in enhancement**: Mistral as progressive enhancement
- **Registry pattern**: Easy to extend with new modes
- **Separation of concerns**: Clean layer boundaries
- **Graceful degradation**: Works without API keys

### 4. **Enterprise Considerations**
- **Data control**: Maps to Mistral's enterprise value proposition
- **Cost awareness**: Low temperature for fidelity tasks, configurable models
- **Error handling**: Network, rate limit, authentication errors handled
- **Security**: Proper key management, no secrets in code
- **Scalability**: Registry pattern allows easy mode extension

### 5. **Deployment Strategy**
- **Zero infrastructure**: No servers, containers, or complex setup
- **Single command**: Simple startup for end users
- **Cross-platform**: Works on Windows, macOS, Linux
- **User-friendly**: Non-technical users can operate it

## Development Workflow

### Running Tests
```bash
# Backend tests
cd backend
venv\Scripts\python verify_backend.py

# Refinement tests (no API key required)
venv\Scripts\python test_refinement.py
```

### Adding New Refinement Modes
1. Add new mode to `RefinementMode` enum in `services/refine.py`
2. Add configuration to `PROMPT_TEMPLATES` dictionary
3. That's it! Mode automatically appears in UI

### Project Structure
- Follows existing patterns for consistency
- Small, single-purpose functions
- Type hints throughout
- Readable by non-engineers

## Roadmap

### Completed ✅
- M0: Full codebase review and documentation
- M1: Plumbing refactoring and quality improvements
- M2: Mistral client + all 5 refinement modes
- M3: Complete mode implementation (all modes in M2)

### Future Enhancements
- Chunking for long transcripts (context window management)
- Session-only API key input in UI
- OS keychain integration for key persistence
- Audio playback during recording
- File size limits and validation
- Concurrent transcription management

## Support

### Troubleshooting
- **Whisper models**: First run downloads models automatically (can be several GB)
- **Memory issues**: Use smaller models if you have limited RAM
- **Mistral API**: Ensure API key is set and valid
- **Port conflicts**: Change ports in `start.bat` if 8000/5173 are in use

### Getting Help
1. Check this README for common issues
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Check browser console and backend logs for errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure no regressions
5. Submit a pull request

## License

This project is provided as-is for portfolio and interview purposes.

## Credits

- **Transcription**: [OpenAI Whisper](https://github.com/openai/whisper)
- **LLM Refinement**: [Mistral AI](https://mistral.ai/)
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Frontend Framework**: [React](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)

---

*Built with care for the AI Deployment Strategist role*  
*Demoable in under a minute, explainable line by line*