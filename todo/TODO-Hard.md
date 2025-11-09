# Hard Tasks

## Video Recording with MediaRecorder API

**Status:** Not Started

**Description:** Implement full MediaRecorder-based video recording (with audio) for job submissions, similar to how audio recording is currently implemented. This would provide a more integrated recording experience with preview, retry, and stop controls, rather than relying solely on the browser's native camera interface via the `capture` attribute.

**Requirements:**
- Use MediaRecorder API to capture video with audio tracks
- Provide recording controls (start, stop, retry, cancel) similar to audio recorder
- Show recording preview before submission
- Handle permissions for both camera and microphone
- Compress video files appropriately for web upload
- Ensure mobile browser compatibility
- Provide fallback to file upload if MediaRecorder is not supported

**Technical Notes:**
- Current implementation uses `capture="environment"` attribute which opens native camera interface
- MediaRecorder API support varies across browsers and devices
- Video files are significantly larger than audio files, requiring compression strategies
- Need to handle both video and audio tracks simultaneously

**Related Files:**
- `marketplace-py/static/audio/audio-recorder.js` - Reference implementation for audio
- `marketplace-py/templates/jobs/submit_job.html` - Current submission form
- `marketplace-py/templates/jobs/create_job.html` - Similar pattern for reference media
