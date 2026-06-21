# Coding-Agent Prompt 3 — Editable transcripts + drop the "Whisper" branding

*Follow-on to Prompts 1 and 2. Paste everything below the line into a CLI coding agent — **Claude Code or Mistral Vibe** — in the transcriber's repository. Commit first: `git add -A && git commit -m "before prompt 3"`.*

---

<role>
You are a staff engineer who specialises in lean, readable Python and frontend code. You make precise, surgical changes to a working app, you never break existing behaviour, and every change earns its place.
</role>

<mission>
Two focused changes on top of the existing app:
1. Make a transcript **manually editable** — an Edit/Save control — and make the **edited version the canonical one** used for both .docx export and Mistral refinement.
2. **Remove the "Whisper" branding from generic, user-facing places** (app/product name, page title, command-line name, the Clean-transcript description), while keeping "Whisper" only where it accurately names the local transcription engine. Surgical edits only.
</mission>

<context>
This follows Prompt 1 (Mistral refinement layer + `mistral_client`) and Prompt 2 (Settings API-key field + selectable Whisper/Voxtral engines). The app is a FastAPI backend + separate frontend; transcripts are produced by either the local Whisper engine or the Mistral Voxtral engine, then viewed, exported to .docx, and optionally refined.
</context>

<hard_constraints>
1. **Preserve all existing behaviour**: transcription (both engines), drag-and-drop, paste, recording, view, .docx export, refinement modes, Settings/API-key. No regressions.
2. **Surgical changes only** — touch the minimum needed for these two features; no refactors, no scope creep.
3. **Lean, readable** Python/JS, type hints where the codebase uses them; no new dependencies; no new infrastructure (no Docker, DB, queue, framework).
4. Keep the changes reviewable; record any assumption in `ASSUMPTIONS.md` and proceed (don't pepper with questions).
</hard_constraints>

<feature_1_editable_transcript>
- On the transcript view, add an **"Edit"** control that turns the displayed transcript into an editable text area, plus **"Save"** and **"Cancel"**.
- **Saving persists the edited text** as the canonical transcript for that file (update the stored transcript via a backend endpoint, e.g. a PUT/PATCH on the existing transcript/job resource), so a refresh shows the edited version.
- **Everything downstream uses the saved (edited) text**: .docx export exports the edited version, and any Mistral refinement mode runs on the edited version — not the original machine output.
- Keep it simple: saving updates the working transcript in place. (If preserving the untouched original is trivial in your data model, keep it as a backstop, but do not add complexity for it.)
- Edit/Save must work regardless of which engine produced the transcript, and must not disturb View, Export, or the refinement flow.
</feature_1_editable_transcript>

<feature_2_remove_whisper_branding>
Make these **generic/branding** mentions engine-neutral. Examples (find all equivalents, don't rely on this list being complete):
- Page/title: "WHISPER TRANSCRIBER" -> "TRANSCRIBER".
- Command line / terminal window title / any printed banner / `start.bat` title: "Whisper Transcriber" -> "Transcriber".
- Clean-transcript mode description: "...fixing Whisper errors" -> "...fixing transcription errors" (or similar engine-neutral wording).
- Any other user-facing app name, header, README title, or window caption that brands the product as "Whisper ...".

**Do NOT remove "Whisper" where it correctly identifies the local engine** — keep it in: the engine selector option (e.g. "Local (Whisper)"), the `WhisperEngine` class/module names, imports, dependency names, and code comments that genuinely refer to the Whisper model. Those are accurate, not branding.

Approach: search the codebase for "Whisper" / "whisper", and for each occurrence decide **branding (rename) vs engine reference (keep)**. Make targeted edits; **do not run a blind global find-replace** (it would break engine labels, class names, and imports).
</feature_2_remove_whisper_branding>

<process>
- **M0 — Locate**: find (a) the transcript view component, the export call, and the refinement call (to confirm they read from one transcript source); and (b) every "Whisper" occurrence, tagged branding-vs-engine. Write a one-paragraph plan. **Gate: the plan + a checklist of current features.**
- **M1 — Editable transcript**: Edit/Save/Cancel UI + persist endpoint; confirm export and refinement both read the saved text. **Gate: edit a transcript, save, refresh (edit persists); export .docx and run a refinement mode — both use the edited text.**
- **M2 — Rename**: apply the surgical branding changes; leave engine references intact. **Gate: no user-facing "Whisper" branding remains (title, CLI name, mode text); the engine selector still correctly shows the local engine; the app builds and runs.**
- **M3 — Verify**: run the app; confirm every prior feature still works. Update README/TALKING-POINTS only where wording referenced the old name. **Gate: fresh run-through works; lint/types/tests green.**
</process>

<acceptance_criteria>
1. A transcript can be edited in the UI and saved; the edit persists across refresh.
2. .docx export and Mistral refinement both operate on the **edited** transcript, not the original machine output.
3. User-facing branding no longer says "Whisper" (page title, command-line/window name, Clean-transcript description, any product header).
4. "Whisper" is retained where it accurately names the local engine (selector label, class/module, imports, comments); no global find-replace damage.
5. Every pre-existing feature still works (both engines, drag/drop/paste/record, view, export, refinement, settings). Changes are surgical; nothing else altered.
6. Lean and readable; no new dependencies or infrastructure.
</acceptance_criteria>

<failure_modes_to_avoid>
- A blind global replace of "Whisper" that breaks the engine selector, `WhisperEngine`, imports, or dependencies.
- Export or refinement still reading the original transcript after an edit.
- Edits not persisting (lost on refresh).
- Breaking either transcription engine or any current feature.
- Scope creep / refactoring beyond these two changes.
- Asking questions you can decide and record.
</failure_modes_to_avoid>
