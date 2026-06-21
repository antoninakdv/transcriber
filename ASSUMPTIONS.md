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

*Last updated: 2026-06-19*