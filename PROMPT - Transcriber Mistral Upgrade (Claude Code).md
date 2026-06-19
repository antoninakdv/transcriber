# Claude Code Prompt — Review & Upgrade the Whisper Transcriber with a Mistral Refinement Layer

*Paste everything below the line into Claude Code, running in the transcriber's repository. One focused session. The goal is a lean, readable, interview-grade upgrade — not a rewrite.*

---

<role>
You are a staff engineer who specialises in lean Python and pragmatic LLM integration. You write code a smart non-engineer can read and explain line by line. You despise overengineering: every abstraction, dependency and line must earn its place. You treat an existing, working tool with respect — you improve its plumbing without changing what it does for the user.
</role>

<mission>
This repo is a lightweight, local audio transcriber: it uses Whisper to turn audio into text and exports to .docx, with drag-and-drop, paste, and in-app audio recording. Do two things:
1. **Tighten the existing code** to a lean, well-structured, readable standard — without changing any current behaviour ("plumbing only").
2. **Add an optional "Refine with Mistral" layer** that post-processes a transcript through Mistral's API using a small set of well-engineered, selectable prompt modes.
This will be a public portfolio piece and an interview talking point for an AI Deployment Strategist role, so correctness, clarity and sound LLM-engineering matter more than feature count.
</mission>

<hard_constraints>
1. **Preserve every existing feature exactly**: Whisper transcription, drag-and-drop, paste, audio recording, text output, .docx export. No regressions. Prove it with a behaviour checklist and/or characterisation tests.
2. **Add the Mistral refinement layer** (spec below).
3. **No new operational complexity**: no Docker, containers, services, queues, databases, build steps, or web frameworks that aren't already present. Detect the existing UI/interface technology and reuse it.
4. **Lean and efficient**: small single-purpose functions, clear names, type hints throughout; delete dead code and duplication; add exactly one dependency — the official Mistral Python SDK (`mistralai`).
5. **Python, readable**: idiomatic, commented only where non-obvious, no clever obscurity. The tool's owner (a strong non-engineer) must be able to read and explain every file.
6. **Existing features change at the plumbing level only** — internal structure and quality, never behaviour.
7. **No secrets in code; secure key handling.** Mistral key via env (`MISTRAL_API_KEY`) / a gitignored `.env` as the primary method. Optionally allow entry through the UI as a **session-only, masked (password-field) override** held in memory and not persisted; if the user chooses to remember it, store it in the **OS keychain** (e.g. Python `keyring` / Windows Credential Manager), never in a plaintext file. Never log, echo, or commit the key; add `.env` and any secrets/config file to `.gitignore`. Transcription must still work fully with no key — Mistral features simply disable cleanly.
</hard_constraints>

<mistral_refinement_spec>
A post-transcription step the user triggers on any transcript (from file, paste, or recording). The user picks a mode; the refined result appears in the UI and is exportable to .docx exactly like the raw transcript. Implement the modes as a **registry of prompt templates** — adding a mode is one new entry, zero changes elsewhere.

Modes:
1. **Meeting notes / bullet points** — a structured summary (key points, decisions, topics) as clean, headed bullets.
2. **Clean transcript (reads as normal speech)** — return the FULL transcript rewritten to read naturally: infer the likely intended words Whisper missed from context, and remove filler, false starts and self-repetition (e.g. "future.. future of... future of real estate" -> "future of real estate"). Preserve all meaning and content. Do NOT summarise and do NOT add facts.
3. **Action items** — extract a structured checklist (task; owner if stated; due date if stated). Structured/JSON output, rendered to a list and to .docx.
4. **Prompt generator** — treat the transcript as raw spoken intent and produce a high-quality, best-practice prompt (role, context, task, explicit constraints, desired output format) ready to paste into any LLM.
5. **Custom instruction** — a free-text box; apply the user's own instruction to the transcript.

Behaviour: model and temperature configurable per mode (low, 0–0.2, for fidelity tasks — clean transcript, action items; modest for notes and prompt-gen). Chunk long transcripts within the model's context window with a documented strategy. Surface network/auth/rate-limit errors clearly without crashing. The raw transcript is never lost or overwritten by a refinement.

**Whisper-only is a first-class mode, not just a fallback.** Using Mistral is always opt-in, per action. The core flow — record / drag-drop / paste -> Whisper transcription -> view -> export to .docx — must run start to finish with no Mistral call and with no key configured. The user can deliberately stay Whisper-only even when a key IS set; refinement is an optional extra the user explicitly chooses, never an automatic step.
</mistral_refinement_spec>

<prompt_engineering_standards>
The LLM prompts themselves must follow evidence-based practice:
- **System/user separation**: a role-setting system prompt per mode; the transcript passed as clearly delimited user input, never blended with instructions.
- **Specific, unambiguous instructions** stating both what to do and what NOT to do (e.g. "do not invent content not present in the transcript").
- **Few-shot exemplars** for the format-sensitive modes (clean transcript; action items) — one short before/after example each.
- **Explicit output contract**: a JSON schema for action items; clearly formatted markdown for notes; a labelled, sectioned prompt for the prompt-generator.
- **Determinism for fidelity**: low temperature, sensible max-tokens, and return only the final artefact (no visible chain-of-thought).
- **Guardrails**: clean-transcript and notes must not add information; on an empty or garbled transcript, say so rather than fabricate.
- Keep each mode's prompt in its own readable, version-commented template (prompts are data, not buried in logic).
</prompt_engineering_standards>

<architecture>
Keep the plumbing lean and one-directional:
- Small modules with single responsibilities: the existing **transcription** logic (Whisper); a thin **`mistral_client`** wrapping the official `mistralai` SDK (config, call, timeout, retry, typed errors); a **`refine`** module holding the mode registry and prompt templates; and the existing **UI/CLI** wiring, behaviourally untouched.
- Dependencies flow one way: UI -> services -> client; templates are data.
- Config via a simple env read (or pydantic-settings if already present); fail clearly on misconfiguration; ship an exhaustive `.env.example`.
- **Consult the CURRENT Mistral documentation and SDK** for exact model IDs, the chat-completions call signature, and structured-output support — do not hard-code names or call shapes from memory.
- **Local-first / data-control by design** (this is also the headline interview point): the default path is fully local (Whisper); Mistral calls are explicit, per-action, opt-in; nothing is logged or persisted beyond what the tool already does; the UI states plainly when text will be sent to Mistral's API. This mirrors Mistral's own enterprise data-control value proposition.
- **Startup stays simple — tidy the launcher only.** Keep the current run architecture (the existing two processes / frontend + backend). Improve only the launcher so a single command starts both **quietly** (minimised or in the background, not two visible terminal windows) and **auto-opens the browser** at the right localhost URL. Do NOT collapse frontend and backend into one process, add a build step, introduce static-file serving, or package into an executable — on a local tool that adds complexity for no real gain.
</architecture>

<process>
Work in order; each gate passes before the next. Record decisions in `ASSUMPTIONS.md` as you go — decide and proceed, ask only before anything destructive or irreversible.
- **M0 — Review**: read the whole repo; write `REVIEW.md` (what it does, the stack, the existing UI technology, dead code / duplication / risks, and the precise plumbing to tighten without behaviour change). **Gate: review doc + a checklist of every current user-facing feature.**
- **M1 — Plumbing refactor**: tighten internals with zero behaviour change; add a characterisation test or scripted manual checklist proving each existing feature is identical. **Gate: every current feature verified unchanged.**
- **M2 — Mistral client + one mode**: implement the client and the "Clean transcript" mode end-to-end, key from env, graceful with no key. **Gate: clean-transcript works on a sample; disables cleanly without a key.**
- **M3 — Remaining modes**: notes, action items (structured), prompt-generator, custom — all via the registry; refined output exports to .docx. **Gate: every mode produces correct, well-formed output on a sample transcript.**
- **M4 — Polish & handover**: `README.md` in deployment-strategist framing (problem, approach, stack, value/time saved); `ARCHITECTURE.md` (one page + a simple data-flow); `TALKING-POINTS.md` for the interview. **Gate: a fresh run-through of the README quickstart actually works; lint, types and tests are green.**
Throughout: type hints everywhere; functions and modules small; only the Mistral SDK added; no secrets.
</process>

<acceptance_criteria>
1. Every pre-existing feature works exactly as before (checklist verified, executed not asserted).
2. "Refine with Mistral" offers the five modes plus custom; each yields correct output; action items are structured; refined text exports to .docx.
3. The tool runs fully locally as a Whisper-only transcriber with no Mistral key — a first-class, selectable mode, and the user can stay Whisper-only even when a key is set (refinement is always opt-in, never automatic).
4. Code is lean, typed and readable; no Docker / new infra / new framework; the only added dependency is the Mistral SDK; no secrets in code.
5. Key handling is safe: env/`.env` (gitignored) primary; optional UI entry is masked and session-only (or OS-keychain if remembered); the key is never logged, echoed or committed.
6. The LLM prompts follow the standards above (system/user split, few-shot where needed, structured output, low temperature for fidelity, no fabrication).
7. `README.md`, `ARCHITECTURE.md` and `TALKING-POINTS.md` exist; the quickstart has been executed and works.
8. Startup is a single quiet command that auto-opens the browser; the two-process architecture is unchanged (no single-process refactor, build step, or executable packaging).
</acceptance_criteria>

<failure_modes_to_avoid>
- Breaking or subtly changing any existing feature. Plumbing only.
- Adding infrastructure or complexity (Docker, servers, databases, queues, a new UI framework, heavy dependencies). Small and boring is correct.
- Over-abstracting "for the future". Build exactly these modes.
- Prompts that let the model invent content in clean-transcript or notes, or that blend instructions with the transcript text.
- Hard-coding Mistral model IDs or SDK call shapes from memory instead of from the current docs.
- Secrets in code; committing a key (ensure `.env` and any secrets file are gitignored); logging or echoing the key or transcript content; sending data anywhere but the chosen Mistral API.
- Re-plumbing the working run model: collapsing the two processes into one, adding a build step or static-file serving, or packaging into an `.exe`. Tidy the launcher, leave the architecture alone.
- Asking the user questions you can resolve by deciding and recording.
</failure_modes_to_avoid>

<interview_deliverables>
Why this piece works for the AI Deployment Strategist role, and what to produce so you can speak to it:
- **It is the role in miniature**: an LLM wired into a real workflow (voice -> transcript -> Mistral refinement -> document), with explicit value framing — exactly what a deployment strategist does for customers.
- **`README.md`** in their language: the problem, the "art of the possible", the approach, the stack, and the value/time saved.
- **`TALKING-POINTS.md`**: model choice and trade-offs; the prompt-engineering decision behind each mode; temperature/determinism; chunking for context limits; structured outputs; error and cost handling; and the local-first / data-control design that maps directly onto Mistral's enterprise proposition.
- Keep it **demoable in under a minute** and **explainable line by line** — you must be able to walk an interviewer through every file.
</interview_deliverables>
