# Coding-Agent Prompt 4 — Play the audio snippet for each transcript segment

*Follow-on to Prompts 1-3. Paste everything below the line into a CLI coding agent — **Claude Code or Mistral Vibe** — in the transcriber's repository. Commit first: `git add -A && git commit -m "before prompt 4"`.*

---

<role>
You are a staff frontend-leaning engineer who makes precise, additive changes to a working app. You never break existing behaviour, you keep code lean and readable, and every change earns its place.
</role>

<mission>
Add a small **play button to each transcript segment** that, when clicked, plays just that snippet of the source audio — seeking to the segment's start time and stopping at its end. Purely additive UI; change nothing else.
</mission>

<context>
This follows Prompts 1-3. The app is a FastAPI backend + separate frontend. The transcript view already renders timestamped segments (e.g. `[00:14 - 00:20]`), and the source audio is already served (there is a file-level "Play" button, so an audio URL/endpoint exists). Transcripts come from either the Whisper or Voxtral engine, both of which produce per-segment start/end times in seconds.
</context>

<hard_constraints>
1. **Preserve all existing behaviour**: transcription (both engines), drag/drop/paste/record, view, edit/save, .docx export, refinement modes, settings, the file-level Play. No regressions.
2. **Purely additive and surgical** — add the per-segment play control and its wiring only; no refactors, no scope creep.
3. **Lean, readable** code; no new dependencies; no new infrastructure. Use the native HTML5 `<audio>` element, not a media library.
4. Reuse the **existing audio endpoint/URL** that the file-level Play button already uses; do not add a new audio-serving mechanism.
5. Record any assumption in `ASSUMPTIONS.md` and proceed; don't pepper with questions.
</hard_constraints>

<feature_spec>
- Add a small **play button (▶) on each transcript segment/line.**
- On click: set the audio's `currentTime` to that segment's **start** time and play; **automatically pause when playback reaches the segment's end** (a `timeupdate` listener). Clicking again replays the snippet.
- **Reuse a single shared `<audio>` element** for all segments (seek + play), rather than one element per line.
- While a snippet is playing, **highlight the active segment** and show the button as a pause/stop state; clicking it again (or starting another segment) stops the current one. Keep this lightweight — a CSS class toggle, no animation framework.
- It must coexist with the existing **file-level Play** control without conflict (one audio element, consistent state).

**Prerequisite to check first:** the frontend needs each segment's **start and end in seconds (numeric)**. If the segment data already carries them, use it. If the view currently only has the formatted `mm:ss` strings, add the raw seconds to the segment data the backend returns (Whisper/Voxtral both provide them) — a minimal change, not a redesign.
</feature_spec>

<process>
- **M0 — Locate**: find the transcript-view component, the segment data shape (does it include numeric start/end seconds?), and the existing audio URL/endpoint + file-level Play. Write a one-paragraph plan. **Gate: plan + confirmation of whether segment seconds are already available.**
- **M1 — Data (only if needed)**: ensure each segment exposes numeric `start`/`end` seconds to the frontend. **Gate: a segment object in the frontend has usable numeric start/end.**
- **M2 — Per-segment playback**: shared `<audio>`, per-segment ▶ button, seek-to-start, auto-stop at end, replay, active-segment highlight, coexistence with file-level Play. **Gate: clicking a segment plays exactly that snippet and stops at its end; works for both an edited and unedited transcript and for audio from either engine.**
- **M3 — Verify**: run the app; confirm every prior feature still works untouched. **Gate: fresh run-through green; lint/types/tests pass.**
</process>

<acceptance_criteria>
1. Each transcript segment has a play button; clicking it plays only that segment's audio and stops at the segment end; clicking again replays it.
2. A single shared `<audio>` element is used; the active segment is visually highlighted; the existing file-level Play still works with no conflict.
3. Segment start/end seconds are available to the frontend (used as-is if present, added minimally if not).
4. Every pre-existing feature is unchanged; the change is additive and surgical.
5. Lean and readable; native HTML5 audio; no new dependencies or infrastructure.
</acceptance_criteria>

<failure_modes_to_avoid>
- Creating one `<audio>` element per segment, or adding a media library, instead of reusing one native element.
- A new/duplicate audio-serving endpoint instead of reusing the existing one.
- Snippets that don't stop at the segment end, or that fight with the file-level Play for control.
- Relying on parsing the `mm:ss` display strings instead of using numeric seconds.
- Touching transcription, export, refinement, or any unrelated code.
- Asking questions you can decide and record.
</failure_modes_to_avoid>
