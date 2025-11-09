# Language + Audio Plan (Django)

## Core Goal
Deliver a reusable Django subsystem that lets any piece of content expose spoken-audio. Users should see a speaker icon; clicking it streams the attached language track. If no audio exists, we surface a polite fallback and invite users (or staff) to request/record the missing translation.

## Phase 1 – Data + Storage
- Add an `AudioSnippet` model keyed by `content_type`, `object_id`, `target_field`, `language_code`, `transcript`, `status`, and `file` (stored via `FileField` to S3/Cloudflare R2/local per settings).
- `target_field` is a short slug (`title`, `description`, etc.) that tells us which UI element or model field the audio is narrating, so one object can expose multiple snippets without collisions.
- Create a lightweight `AudioRequest` model to log “needs translation/audio” so we can track gaps separately from finished snippets.
- Provide signals/helpers (e.g., `AudioMixin`) so any model can declare it supports spoken audio.

## Phase 2 – Admin + Workflow
- Build Django admin inlines/forms so staff can upload MP3/OGG files, preview them, and mark status (`draft`, `ready`, `needs_review`).
- Allow staff to create `AudioRequest` entries directly from missing languages; auto-close when an `AudioSnippet` for that target exists.
- Optional Celery task: when a request is logged, trigger notifications or TTS generation to seed a draft file.

## Phase 3 – API + Serving
- Expose a REST endpoint (DRF) that, given `content_type/object_id/language`, returns the audio URL, metadata, and fallback text.
- Secure URLs via signed storage links or proxy view to avoid leaking private buckets.
- Cache per-object language lookups (Redis) to minimize DB hits when rendering pages.

## Phase 4 – Front-End Experience
- Component injects a speaker icon next to any field flagged as having audio and includes `data-audio-target="title"` (or similar) so the API can request the correct snippet.
- On click, load the audio via HTML `<audio>` tag or custom player; handle streaming + loading state.
- If snippet missing, show toast/banner: “Sorry, not recorded yet. Want to help?” with CTA to open the request form.
- Include graceful fallback for screen readers and offline mode.

## Monitoring + QA
- Nightly job to verify audio files still exist in storage; flag broken links.
- Unit tests for model logic, API responses, and permission boundaries.
- Browser tests (Playwright) to cover playback + fallback behavior.

## Extended / Optional Enhancements
- In-app upload wizard so approved users can record or upload new files directly; enforce duration/format validation server-side.
- Workflow to “connect” newly uploaded files: user selects the target object + language, system auto-creates the `AudioSnippet`, updates related requests, and notifies reviewers.
- Batch importer to ingest existing ZIP folders of audio and attach them using a CSV mapping.
- Community contribution: let authenticated volunteers submit translations; route submissions into moderation queue and auto-create review tasks.

## Pending TODO
- Ensure that when a user selects any language other than Spanish or English, the written UI content remains in Spanish while the audio snippets (and spoken playback) switch to the selected language so that all alternate languages are available through audio even when text falls back to Spanish.