# Coding-Agent Prompt 2 — Settings API-key field + Mistral (Voxtral) transcription option

<role>
You are a staff engineer who specialises in lean Python and pragmatic LLM integration. You write code a smart non-engineer can read and explain line by line. Every dependency and line must earn its place. You extend an existing, working tool without changing what it already does for the user.
</role>

<mission>
Build on the previous upgrade. Add exactly two capabilities:
1. A **Settings UI field to enter the Mistral API key**, with secure handling.
2. A **user-selectable transcription engine** — keep local Whisper as the default, and add **Mistral's Voxtral speech-to-text API** as an option.
Preserve everything else. Stay lean, readable, and add no new infrastructure.
</mission>

<context>
This follows Prompt 1, which added the Mistral refinement layer and a thin `mistral_client`, plus config/key plumbing. **Reuse that client and config — do not duplicate them.** The app already has a Settings panel and a `/api/settings` endpoint (FastAPI backend, separate frontend); extend those rather than building new ones.
</context>

<hard_constraints>
1. **Preserve all existing behaviour**: Whisper transcription, drag-and-drop, paste, recording, text output, .docx export, and the Prompt 1 refinement modes. No regressions.
2. **Whisper-only stays fully functional with no key** — it remains the default, offline path.
3. **Lean, readable Python**, type hints, small single-purpose functions. No new dependencies beyond what's needed for secure key storage (e.g. `keyring`); reuse the Mistral SDK already added.
4. **No new operational complexity**: no Docker, databases, queues, services, build steps, or new UI framework. Reuse the existing stack.
5. **Secure key handling** (see Feature 1) — non-negotiable.
6. **Consult the CURRENT Mistral docs and SDK** for the Voxtral model IDs and the speech-to-text call signature — do not hard-code them from memory.
</hard_constraints>

<feature_1_api_key_in_settings>
- Add a **masked (password-style) field** in the Settings panel to enter the Mistral API key, with a Save action.
- **Precedence**: an environment variable / gitignored `.env` remains the primary source; the Settings field is an override.
- **Persistence**: default to **in-memory for the session**. Offer a "Remember on this device" toggle that stores the key in the **OS keychain** (Windows Credential Manager via `keyring`) — never a plaintext file, never committed.
- **The `/api/settings` endpoint must never return the stored key to the browser.** Return only whether a key is set (boolean) and, at most, a masked hint (e.g. last 4 chars). Saving sends the new key from the UI to the backend over localhost only.
- Add a **"Test connection"** action that validates the key with one lightweight Mistral call and shows a clear success/failure result.
- Show a **status indicator**: "Mistral connected" vs "No key — Whisper only, refinement disabled."
- Never log or echo the key. Ensure `.env` and any secrets file are in `.gitignore`.
</feature_1_api_key_in_settings>

<feature_2_voxtral_transcription_option>
- Make the **transcription engine selectable**: "Local (Whisper)" — the **default** — and "Mistral (Voxtral, cloud)". Put the default-engine choice in Settings; allow a per-transcription override only if the existing UI makes that simple, otherwise a global default is fine.
- The **local Whisper path is unchanged.** The Voxtral path calls Mistral's speech-to-text API (look up the current model IDs — e.g. the Voxtral Transcribe / Realtime models — and the exact call from the live docs).
- Voxtral **requires the API key** from Feature 1. With no key, the Voxtral option is **disabled with a clear hint**, and Whisper stays available.
- **Both engines feed the same downstream flow**: text output -> view -> .docx export -> the Prompt 1 refinement modes. The engine choice only changes how audio becomes text; nothing downstream should care which engine produced it.
- Implement the engine as a **small pluggable interface** (e.g. `transcribe(audio) -> result`) with two implementations — `WhisperEngine` (existing logic, moved behind the interface with no behaviour change) and `VoxtralEngine` (API) — selected from settings, so adding another engine later is one new class.
- Accurate basic transcription is the requirement; Voxtral extras (speaker diarization, word-level timestamps, language selection) are optional nice-to-haves only if cheap and they don't bloat the UI.
</feature_2_voxtral_transcription_option>

<architecture_notes>
- One source of truth for the key and the Mistral config: reuse Prompt 1's `mistral_client` for both the key plumbing and the Voxtral calls.
- Keep the **local-first** posture: Whisper local is the default and the privacy story; Voxtral is opt-in, and the UI states plainly when audio will be sent to Mistral's API.
- Prompts/templates and config stay as data, separate from logic; functions small and typed.
</architecture_notes>

<process>
Work in order; each gate passes before the next. Record decisions in `ASSUMPTIONS.md`; decide and proceed, ask only before anything destructive.
- **M0 — Review**: locate the Settings UI, `/api/settings`, the `mistral_client`, and the current transcription call; write a short plan. **Gate: plan + a checklist of every current user-facing feature.**
- **M1 — API key in Settings**: masked field, secure save (session default; optional keychain), Test-connection, status indicator; endpoint never returns the raw key. **Gate: entering a key and testing succeeds; with no key the app still works as a Whisper-only transcriber; the key is never logged or returned in plaintext.**
- **M2 — Voxtral engine**: the engine interface + `VoxtralEngine` via the current Mistral STT API; engine selector in Settings; Whisper default and unchanged. **Gate: transcribe the same file with each engine — both produce text and both export to .docx; Voxtral is cleanly disabled without a key.**
- **M3 — Docs**: update `README.md`, `ARCHITECTURE.md` and `TALKING-POINTS.md` to cover secure key handling and the local-vs-cloud engine choice. **Gate: a fresh quickstart run works; lint, types and tests green.**
Throughout: type hints; small functions; reuse, don't duplicate; build the Voxtral call from current docs.
</process>

<acceptance_criteria>
1. Settings has a masked Mistral API-key field; env/`.env` remains primary; an optional "remember" uses the OS keychain; the key is never logged, echoed, returned to the browser in plaintext, written to a plaintext file, or committed.
2. "Test connection" validates the key and shows a clear result; the status indicator reflects connected / no-key.
3. The transcription engine is selectable — Whisper (default, offline) and Voxtral (cloud, needs key) — and Voxtral is disabled cleanly with no key.
4. Both engines feed the same text -> view -> .docx -> refinement flow; every pre-existing feature is unchanged (verified, not assumed).
5. Code is lean, readable and typed; no new infra; the Voxtral call is built from current Mistral docs, not memory.
6. `README.md`, `ARCHITECTURE.md` and `TALKING-POINTS.md` are updated and the quickstart has been executed.
</acceptance_criteria>

<failure_modes_to_avoid>
- Returning, logging, or echoing the API key in plaintext; committing it; or storing it in a plaintext file.
- Breaking the existing Whisper flow or any current feature.
- Hard-coding Voxtral model IDs or the STT endpoint from memory instead of the current docs.
- Duplicating key/config plumbing instead of reusing Prompt 1's `mistral_client`.
- Adding infrastructure, dependencies, or a new framework beyond secure key storage.
- Making Voxtral mandatory or removing the local/offline Whisper path.
- Asking questions you can resolve by deciding and recording.
</failure_modes_to_avoid>

<interview_note>
The selectable engine (local Whisper vs Mistral Voxtral) plus transparent, secure key handling is the AI-Deployment-Strategist story in miniature: choosing the right model for the customer's constraint — privacy/offline/cost vs cloud quality and features — with enterprise-grade data hygiene. Capture this, and the local-first rationale, in `TALKING-POINTS.md`.
</interview_note>
