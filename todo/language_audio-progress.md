# Language + Audio Plan - Progress Tracking

## Core Goal
Deliver a reusable Django subsystem that lets any piece of content expose spoken-audio. Users should see a speaker icon; clicking it streams the attached language track. If no audio exists, we surface a polite fallback and invite users (or staff) to request/record the missing translation.

## Phase 1 ? Data + Storage
- [x] Add an `AudioSnippet` model keyed by `content_type`, `object_id`, `target_field`, `language_code`, `transcript`, `status`, and `file` (stored via `FileField` to S3/Cloudflare R2/local per settings).
- [x] `target_field` is a short slug (`title`, `description`, etc.) that tells us which UI element or model field the audio is narrating, so one object can expose multiple snippets without collisions.
- [x] Create a lightweight `AudioRequest` model to log "needs translation/audio" so we can track gaps separately from finished snippets.
- [x] Provide signals/helpers (e.g., `AudioMixin`) so any model can declare it supports spoken audio.

**Current Status:** ✅ Completed

## Phase 2 – Admin + Workflow
- [x] Build Django admin inlines/forms so staff can upload MP3/OGG files, preview them, and mark status (`draft`, `ready`, `needs_review`).
- [x] Allow staff to create `AudioRequest` entries directly from missing languages; auto-close when an `AudioSnippet` for that target exists.
- [ ] Optional Celery task: when a request is logged, trigger notifications or TTS generation to seed a draft file.

**Current Status:** ✅ Mostly completed (Celery task optional, skipped for now)

## Phase 3 ? API + Serving
- [x] Expose a REST endpoint (DRF) that, given `content_type/object_id/language`, returns the audio URL, metadata, and fallback text.
- [x] Secure URLs via signed storage links or proxy view to avoid leaking private buckets.
- [x] Cache per-object language lookups (Redis) to minimize DB hits when rendering pages.

**Current Status:** ✅ Completed

## Phase 4 – Front-End Experience
- [x] Component injects a speaker icon next to any field flagged as having audio and includes `data-audio-target="title"` (or similar) so the API can request the correct snippet.
- [x] On click, load the audio via HTML `<audio>` tag or custom player; handle streaming + loading state.
- [x] If snippet missing, show toast/banner: "Sorry, not recorded yet. Want to help?" with CTA to open the request form.
- [x] Include graceful fallback for screen readers and offline mode.
- [x] Implement fallback audio playback when audio snippets are missing or fail to load (MP3 format, configurable via settings).

**Current Status:** ✅ Completed (including fallback audio implementation)

## Monitoring + QA
- [ ] Nightly job to verify audio files still exist in storage; flag broken links.
- [ ] Unit tests for model logic, API responses, and permission boundaries.
- [ ] Browser tests (Playwright) to cover playback + fallback behavior.

**Current Status:** Not started

## Extended / Optional Enhancements
- [ ] In-app upload wizard so approved users can record or upload new files directly; enforce duration/format validation server-side.
- [ ] Workflow to "connect" newly uploaded files: user selects the target object + language, system auto-creates the `AudioSnippet`, updates related requests, and notifies reviewers.
- [ ] Batch importer to ingest existing ZIP folders of audio and attach them using a CSV mapping.
- [ ] Community contribution: let authenticated volunteers submit translations; route submissions into moderation queue and auto-create review tasks.
- [ ] Wire the new `/jobs/audio-support/<slug>/` page to actual wallet payments so the "Fondear (10 pesos)" action captures money instead of showing an informational toast.
- [ ] Automate promotion of `AudioContribution` uploads into vetted `AudioSnippet` records (assignment, review queue, notification back to contributor).

**Current Status:** Not started

---

## Notes
- Last updated: Fallback audio implementation completed
- Currently working on: Ready for testing and deployment
- Created `audio` Django app with:
  - `AudioSnippet` model with generic foreign key support
  - `AudioRequest` model for tracking missing audio
  - `AudioMixin` helper class for models
  - Django admin integration with previews and inlines
  - REST API endpoints (DRF) with fallback audio URL support
  - Caching support for performance
  - Template tags for easy integration
  - Front-end JavaScript module for audio playback with fallback handling
  - Accessible UI components with ARIA labels
  - Signals to auto-close requests when snippets are created
  - **Fallback audio system**: MP3 fallback file support (`AUDIO_FALLBACK_FILE` setting)
    - Fallback plays when audio snippets are missing or fail to load
    - Configured in `settings.py` as `'audio/fallback.mp3'`
    - Documentation created at `static/audio/README_FALLBACK.md`
    - Dashboard integration with fallback support
