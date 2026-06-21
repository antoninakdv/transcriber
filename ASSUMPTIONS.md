# ASSUMPTIONS.md - Decisions and Assumptions Made During Development

This document records decisions made during the review and implementation process to maintain transparency and enable future developers (or the tool owner) to understand the reasoning behind key choices.

---

## M0 Review Assumptions

### Architecture Decisions

**ASSUMPTION-001: Preserve Two-Process Architecture**
- **Decision**: Keep separate backend (FastAPI) and frontend (Vite/React) processes
- **Reasoning**: The UPGRADE_PROMPT explicitly states "keep the current run architecture (the existing two processes / frontend + backend)" and "Do NOT collapse frontend and backend into one process"
- **Impact**: No architectural refactoring, only plumbing improvements

**ASSUMPTION-002: Use Existing Service Layer Pattern**
- **Decision**: Follow existing pattern of `services/` directory with single-responsibility modules
- **Reasoning**: Current architecture has clear separation: routers (HTTP) -> services (business logic) -> clients (external)
- **Impact**: New Mistral functionality will follow same pattern

**ASSUMPTION-003: Mistral SDK Already Available**
- **Decision**: The `mistralai` package is already installed in the venv (version 2.4.13)
- **Reasoning**: Detected in `backend/venv/Lib/site-packages/mistralai-2.4.13.dist-info/`
- **Impact**: No need to add to requirements.txt initially, but should be added for reproducibility

### Technology Stack Assumptions

**ASSUMPTION-004: React 19 is Stable**
- **Decision**: Continue using React 19.2.6 as the frontend framework
- **Reasoning**: Already working in the current codebase, no known issues
- **Impact**: No framework changes needed

**ASSUMPTION-005: Vite is the Build Tool**
- **Decision**: Continue using Vite 8.0.12 as the frontend build system
- **Reasoning**: Already configured and working
- **Impact**: No build system changes

**ASSUMPTION-006: FastAPI is the Backend Framework**
- **Decision**: Continue using FastAPI 0.115.12 (or 0.136.1 as seen in venv)
- **Reasoning**: Already working, good async support, type hints
- **Impact**: No framework changes

### User Experience Assumptions

**ASSUMPTION-007: Local-Only Usage**
- **Decision**: This is a local tool, not a web service
- **Reasoning**: Hardcoded localhost CORS, no authentication, file-based storage
- **Impact**: Security model appropriate for local use, no need for production-grade auth

**ASSUMPTION-008: Whisper-Only is First-Class**
- **Decision**: Mistral refinement is opt-in, Whisper-only mode must work without any Mistral key
- **Reasoning**: Explicit requirement from UPGRADE_PROMPT: "Whisper-only is a first-class mode, not just a fallback"
- **Impact**: All Mistral features must gracefully disable when no key is present

**ASSUMPTION-009: Single User Session**
- **Decision**: No multi-user considerations needed
- **Reasoning**: Local tool, single user at a time
- **Impact**: Global state acceptable for this use case

### Code Quality Assumptions

**ASSUMPTION-010: Type Hints Throughout**
- **Decision**: Add type hints to all new code, improve existing where missing
- **Reasoning**: UPGRADE_PROMPT requires "type hints throughout"
- **Impact**: All functions should have proper type annotations

**ASSUMPTION-011: Small Functions**
- **Decision**: Keep functions small and single-purpose
- **Reasoning**: UPGRADE_PROMPT requires "small single-purpose functions"
- **Impact**: Break down large functions, avoid monolithic methods

**ASSUMPTION-012: Readable by Non-Engineers**
- **Decision**: Code must be explainable line-by-line to strong non-engineers
- **Reasoning**: Explicit requirement from UPGRADE_PROMPT
- **Impact**: Avoid cleverness, prefer clarity, add comments where non-obvious

### Mistral Integration Assumptions

**ASSUMPTION-013: Mistral API Key Handling**
- **Decision**: Priority: Environment variable (`MISTRAL_API_KEY`) > Session-only UI input (masked) > OS keychain (optional)
- **Reasoning**: UPGRADE_PROMPT specifies: "env (`MISTRAL_API_KEY`) / a gitignored `.env` as the primary method. Optionally allow entry through the UI as a session-only, masked (password-field) override held in memory... if the user chooses to remember it, store it in the OS keychain"
- **Impact**: Implement key handling with this priority order

**ASSUMPTION-014: No Secrets in Code**
- **Decision**: Never commit API keys, never log them, never echo them
- **Reasoning**: Explicit security requirement
- **Impact**: All key handling must be secure

**ASSUMPTION-015: Model and Temperature Configurable**
- **Decision**: Allow configuration of Mistral model and temperature per refinement mode
- **Reasoning**: UPGRADE_PROMPT: "model and temperature configurable per mode"
- **Impact**: Low temperature (0-0.2) for fidelity tasks, modest for creative tasks

**ASSUMPTION-016: Chunking Strategy Needed**
- **Decision**: Implement chunking for long transcripts within model context window
- **Reasoning**: UPGRADE_PROMPT: "Chunk long transcripts within the model's context window with a documented strategy"
- **Impact**: Need to implement and document chunking approach

### Mode Implementation Assumptions

**ASSUMPTION-017: Registry Pattern for Modes**
- **Decision**: Implement modes as a registry of prompt templates
- **Reasoning**: UPGRADE_PROMPT: "Implement the modes as a registry of prompt templates — adding a mode is one new entry, zero changes elsewhere"
- **Impact**: Each mode is a separate entry in a registry, not hardcoded in UI logic

**ASSUMPTION-018: Five Required Modes**
- **Decision**: Implement exactly these five modes:
  1. Meeting notes / bullet points
  2. Clean transcript (reads as normal speech)
  3. Action items (structured/JSON)
  4. Prompt generator
  5. Custom instruction
- **Reasoning**: Explicit list in UPGRADE_PROMPT
- **Impact**: No more, no less - these are the required modes

**ASSUMPTION-019: Prompt Engineering Standards**
- **Decision**: Follow evidence-based prompt engineering:
  - System/user separation
  - Specific, unambiguous instructions
  - Few-shot exemplars for format-sensitive modes
  - Explicit output contract (JSON schema for action items)
  - Low temperature for fidelity
  - Guardrails against fabrication
- **Reasoning**: Explicit requirements in UPGRADE_PROMPT
- **Impact**: All prompts must follow these standards

**ASSUMPTION-020: Structured Output for Action Items**
- **Decision**: Action items mode produces structured/JSON output
- **Reasoning**: UPGRADE_PROMPT: "Action items — extract a structured checklist... Structured/JSON output, rendered to a list and to .docx"
- **Impact**: Need JSON schema definition and proper rendering

### Process and Workflow Assumptions

**ASSUMPTION-021: Sequential Milestone Completion**
- **Decision**: Work in order M0 → M1 → M2 → M3 → M4, each gate passes before next
- **Reasoning**: Explicit requirement: "Work in order; each gate passes before the next"
- **Impact**: Cannot skip ahead, must complete each milestone fully

**ASSUMPTION-022: Only Add Mistral SDK Dependency**
- **Decision**: The only new dependency allowed is `mistralai`
- **Reasoning**: UPGRADE_PROMPT: "add exactly one dependency — the official Mistral Python SDK (`mistralai`)"
- **Impact**: No other dependencies can be added

**ASSUMPTION-023: No Infrastructure Changes**
- **Decision**: No Docker, containers, services, queues, databases, build steps, or web frameworks that aren't already present
- **Reasoning**: Explicit hard constraint
- **Impact**: Must work with existing architecture only

### Launcher Assumptions

**ASSUMPTION-024: Fix start.bat Paths**
- **Decision**: Use relative paths instead of hardcoded `C:\Whisper\...`
- **Reasoning**: Current paths won't work from different directories
- **Impact**: Launcher should work from project root

**ASSUMPTION-025: Single Quiet Command**
- **Decision**: Launcher should start both processes quietly and auto-open browser
- **Reasoning**: UPGRADE_PROMPT: "Improve only the launcher so a single command starts both quietly (minimised or in the background, not two visible terminal windows) and auto-opens the browser"
- **Impact**: Better user experience, no visible terminal windows

---

## Prompt 2 Assumptions (API key in Settings + Voxtral engine)

**ASSUMPTION-026: Key resolution precedence (env wins)**
- **Decision**: Active key = `MISTRAL_API_KEY` env/`.env` → session key (entered in UI) → keychain.
- **Reasoning**: Prompt 2 states "env / `.env` remains the primary source; the Settings field is an override." Read literally, env stays authoritative for headless/automated use; the UI field is the path for users who won't edit `.env`.
- **Impact**: A key set in the environment cannot be overridden from the UI (documented trade-off). `get_active_key()` in `mistral_client.py` is the single source of truth.

**ASSUMPTION-027: `keyring` added as a dependency**
- **Decision**: Add `keyring` (Windows Credential Manager backend) for the optional "remember on this device".
- **Reasoning**: Prompt 2 explicitly permits "no new dependencies beyond what's needed for secure key storage (e.g. `keyring`)." Prompt 1's one-dependency rule is superseded for this specific purpose.
- **Impact**: Two backend dependencies now (`mistralai`, `keyring`). Remembered keys live in the OS keychain, never a file.

**ASSUMPTION-028: Key never persisted to settings.json**
- **Decision**: The API key is handled by dedicated endpoints (`/api/settings/mistral-key`), never written to `settings.json`.
- **Reasoning**: `settings.json` is plaintext; secrets must not land there.
- **Impact**: `GET /api/settings` returns only `{configured, source, hint(last4)}` — never the raw key.

**ASSUMPTION-029: Engine default is a global setting; per-request override supported**
- **Decision**: `transcription_engine` lives in `settings.json` (default `whisper`). The transcribe endpoint also accepts an optional `engine` override, but the UI uses the global default.
- **Reasoning**: Prompt 2: "Put the default-engine choice in Settings; allow a per-transcription override only if the existing UI makes that simple, otherwise a global default is fine."
- **Impact**: Minimal UI change; the existing Transcribe button honors the configured engine.

**ASSUMPTION-030: Voxtral model + call from current docs/SDK**
- **Decision**: Use `voxtral-mini-latest` via `client.audio.transcriptions.complete(model=, file={content,file_name}, timestamp_granularities=["segment"])`, normalized to `{text, language, segments}`.
- **Reasoning**: Verified against the live Mistral docs and by introspecting the installed `mistralai` 2.4.13 SDK — not from memory.
- **Impact**: Voxtral output flows into the exact same downstream path as Whisper (view → .docx → refinement).

---

## Prompt 3 Assumptions (editable transcripts + drop "Whisper" branding)

**ASSUMPTION-031: Edited text is canonical; segments kept as a backstop**
- **Decision**: A manual edit updates `TranscriptionResult.text` and sets `edited=True`; the original `segments` (with timings) are kept unchanged.
- **Reasoning**: Prompt 3 wants the edited text canonical for export + refinement, while "keeping the untouched original as a backstop if trivial." Segments are the cheap backstop/time reference.
- **Impact**: Refinement already reads `transcription.text`, so it uses the edit automatically. New `PUT /api/transcribe/{file_id}/result` persists the edit.

**ASSUMPTION-032: Edited transcripts export as full text (no stale timestamps)**
- **Decision**: When `edited` (or refined), `generate_docx` renders the full text; an unedited machine transcript keeps the per-segment timestamp layout.
- **Reasoning**: After a free-text edit the segment timings no longer line up with the words; showing them would be misleading.
- **Impact**: Existing (unedited) export behaviour is byte-for-byte preserved; edited export reflects the edit.

**ASSUMPTION-033: "Whisper" branding vs engine reference**
- **Decision**: Renamed user-facing product branding (navbar, API title, `start.bat` titles/banner, Clean-transcript description, README/ARCHITECTURE/.env.example headers) to "Transcriber". Kept "Whisper" everywhere it names the local engine (`WhisperEngine`, `whisper_service`, imports, `openai-whisper`, "Local (Whisper)" selector, "Whisper Model" label, engine comments). No global find-replace.
- **Reasoning**: Prompt 3 Feature 2 — surgical, branding-only.
- **Impact**: `verify_backend.py`'s title assertion was updated to match. The internal keychain service id `whisper-transcriber` was **left unchanged** (not user-facing; renaming would orphan any already-remembered key). `REVIEW.md` and dev verification-script banners were left as historical artifacts.

---

## Prompt 4 Assumptions (per-segment audio snippet playback)

**ASSUMPTION-034: Segment seconds already available — no backend change**
- **Decision**: Reused the existing numeric `start`/`end` on each segment; did not add or change any backend data.
- **Reasoning**: `TranscriptionSegment` already carries float `start`/`end` (both Whisper and Voxtral populate them), so M1 (data) was unnecessary.
- **Impact**: Prompt 4 is a frontend-only change in `TranscriptionView.jsx`.

**ASSUMPTION-035: One shared `<audio>` element, reusing the existing audio URL**
- **Decision**: Added a single hidden `<audio>` in the transcript view, sourced from the existing `getAudioUrl(fileId)`. Each segment ▶ seeks to `start`, plays, and a `timeupdate` listener auto-pauses at `end`; clicking again replays; the active segment gets a `segment--playing` highlight.
- **Reasoning**: Spec requires one shared native element and reuse of the existing endpoint (verified the endpoint returns HTTP 206 for Range requests, so seeking works).
- **Impact**: No media library, no new endpoint, no new dependency.

**ASSUMPTION-036: Segment playback and file-level Play are independent native elements**
- **Decision**: The per-segment feature uses its own shared `<audio>`; the file-level Play (a transient `new Audio()` in `FileList`) is left untouched.
- **Reasoning**: Unifying them would mean lifting audio state across components — beyond a surgical, additive change. They do not break each other.
- **Impact**: If a user deliberately starts the whole-file Play *and* a segment snippet, both could sound at once — a minor, self-inflicted edge case, not a functional regression. Each control on its own behaves correctly.

---

## Decision Log Format

Each decision follows this format:
- **ASSUMPTION-XXX**: Short descriptive title
- **Decision**: What was decided
- **Reasoning**: Why this decision was made (reference to requirements or best practices)
- **Impact**: What this means for implementation
- **Date**: When the decision was made
- **Status**: Active / Superseded / Reversed

## Open Questions (To Be Decided)

None at this time. The UPGRADE_PROMPT provides sufficient guidance for all major decisions.

---

*Last updated: 2026-06-21 (Prompt 3)*