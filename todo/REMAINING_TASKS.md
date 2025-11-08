# Remaining Tasks Summary

## ? Completed Phases
- **Phase 1** ? Data + Storage: ? Complete
- **Phase 2** ? Admin + Workflow: ? Mostly complete (Celery task optional)
- **Phase 3** ? API + Serving: ? Complete (including fallback audio)
- **Phase 4** ? Front-End Experience: ? Complete (including fallback audio)

## ?? Critical Next Steps

### 1. Create Fallback Audio File
**Priority: HIGH** (Required for fallback to work)
- [ ] Create `static/audio/fallback.mp3` file
- [ ] See `static/audio/README_FALLBACK.md` for instructions
- [ ] Recommended: 1-3 second MP3, under 50KB
- [ ] Test fallback playback after adding file

### 2. Testing & QA
**Priority: HIGH** (Before production deployment)
- [ ] Unit tests for model logic, API responses, and permission boundaries
- [ ] Browser tests (Playwright) to cover playback + fallback behavior
- [ ] Test audio playback across different browsers
- [ ] Test fallback audio when snippets are missing
- [ ] Test audio request workflow
- [ ] Test caching behavior

### 3. Monitoring & Maintenance
**Priority: MEDIUM** (Production readiness)
- [ ] Nightly job to verify audio files still exist in storage; flag broken links
- [ ] Set up error logging for audio playback failures
- [ ] Monitor API endpoint performance

## ?? Optional Enhancements

### 4. Celery Integration (Optional)
**Priority: LOW** (Nice to have)
- [ ] Celery task: when a request is logged, trigger notifications or TTS generation to seed a draft file

### 5. Extended Features (Optional)
**Priority: LOW** (Future enhancements)
- [ ] In-app upload wizard so approved users can record or upload new files directly
- [ ] Workflow to "connect" newly uploaded files with auto-creation of AudioSnippet
- [ ] Batch importer to ingest existing ZIP folders of audio with CSV mapping
- [ ] Community contribution: authenticated volunteers submit translations with moderation queue

### 6. Language-Specific Features (From original TODO)
**Priority: MEDIUM** (Feature requirement)
- [ ] Ensure that when a user selects any language other than Spanish or English, the written UI content remains in Spanish while the audio snippets (and spoken playback) switch to the selected language
- [ ] Design a mobile-first audio contribution feature that lets users either upload an existing clip or record directly from their phone browser

## ?? Immediate Action Items

1. **Add fallback audio file** (`static/audio/fallback.mp3`)
2. **Write unit tests** for audio models and API
3. **Write browser tests** for audio playback
4. **Test the complete workflow** end-to-end
5. **Document deployment steps** for production

## ?? Current Status

**Core functionality:** ? Complete
**Fallback system:** ? Complete (needs MP3 file)
**Testing:** ? Not started
**Production readiness:** ?? Needs testing and fallback file
