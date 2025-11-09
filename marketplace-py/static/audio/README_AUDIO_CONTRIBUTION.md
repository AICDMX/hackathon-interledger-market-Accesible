# Mobile-First Audio Contribution Feature

## Overview

A complete mobile-first audio contribution system that allows users to either upload existing audio files or record directly from their phone browser. The feature handles permissions, compression, and background uploads seamlessly.

## Features

### 1. Browser-Based Recording
- Uses MediaRecorder API for native browser recording
- Automatic codec selection (WebM/Opus preferred for compression)
- Real-time duration tracking with 30-second limit
- Visual recording indicator with pulse animation

### 2. Permission Handling
- Graceful permission requests with clear error messages
- Supports multiple error scenarios (denied, no microphone, unsupported browser)
- User-friendly Spanish error messages

### 3. Client-Side Compression
- Automatic compression using Web Audio API
- Optimized bitrate (64 kbps default) for mobile efficiency
- Converts uncompressed formats to WebM/Opus when possible
- Reduces file sizes significantly for mobile uploads

### 4. Background Uploads
- Uses Fetch API with `keepalive: true` for background uploads
- Progress tracking with visual progress bar
- Continues upload even if user navigates away (within browser limits)
- Proper error handling and retry mechanisms

### 5. Mobile-First Design
- Touch-friendly buttons (56px minimum height)
- Responsive layout that adapts to screen sizes
- Follows design tokens from `docs/design.md`
- Safe area support for notched devices
- Reduced motion support for accessibility

## Files Created/Modified

### New Files
1. `static/audio/audio-recorder.js` - Core recording functionality
2. `static/audio/audio-contribution-ui.js` - UI controller and integration
3. `static/audio/audio-contribution.css` - Mobile-first styles

### Modified Files
1. `templates/jobs/audio_support.html` - Added recording UI
2. `audio/views.py` - Added `upload_audio_contribution` API endpoint
3. `audio/urls.py` - Added upload route
4. `marketplace/urls.py` - Added namespace for audio URLs

## API Endpoint

### POST `/api/audio/contributions/upload/`

Uploads an audio contribution (supports both file uploads and browser recordings).

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body:
  - `file` (required): Audio file (WebM, OGG, MP4, WAV, MP3)
  - `language_code` (required): Language code (e.g., 'es', 'nah', 'oto')
  - `notes` (optional): Additional notes
  - `target_slug` (optional): Target identifier slug

**Response:**
```json
{
  "success": true,
  "message": "Audio contribution uploaded successfully",
  "contribution_id": 123,
  "status": "pending"
}
```

**Error Response:**
```json
{
  "error": "Error message here"
}
```

## Usage

### In Templates

The feature auto-initializes when a container has the `data-audio-contribution` attribute:

```html
<div id="audio-contribution-form" 
     data-audio-contribution
     data-target-slug="job_post"
     data-language-code="es"
     data-upload-url="/api/audio/contributions/upload/"
     data-max-duration="30000">
    <!-- Form content -->
</div>
```

### Manual Initialization

```javascript
const ui = new AudioContributionUI('container-id', {
    maxDuration: 30000,
    uploadUrl: '/api/audio/contributions/upload/',
    targetSlug: 'job_post',
    languageCode: 'es'
});
```

## Browser Support

### Recording Support
- Chrome/Edge: ? Full support (WebM/Opus)
- Firefox: ? Full support (WebM/Opus)
- Safari: ?? Limited (MP4, may require user interaction)
- Mobile Chrome: ? Full support
- Mobile Safari: ?? Limited (iOS 14.3+)

### Fallback
If recording is not supported, users can still upload audio files using the traditional file input.

## Design Tokens Used

- Colors: `--color-primary`, `--color-success`, `--color-error`
- Spacing: `--space-2` through `--space-8`
- Border radius: `--radius-input`, `--radius-card`, `--radius-pill`
- Motion: `--motion-default`, `--motion-fast`
- Shadows: `--shadow-card`

## Accessibility Features

- ARIA labels and roles for screen readers
- Keyboard navigation support
- Focus indicators with high contrast
- Reduced motion support
- Semantic HTML structure
- Progress announcements for uploads

## Audio Quality Settings

### High-Quality Recording
- **Sample Rate**: 48 kHz (ideal) with 44.1 kHz fallback (CD quality)
- **Bitrate**: 192 kbps (near-transparent quality for voice)
- **Codec**: Opus (WebM/Opus preferred) - excellent quality-to-size ratio
- **Audio Processing**: 
  - Echo cancellation
  - Noise suppression
  - Auto gain control
  - High-pass filter (removes low-frequency noise below 80Hz)
  - Low-pass filter (removes high-frequency noise above 12kHz)
  - Dynamics compressor for consistent levels

### Quality Comparison
- **Previous**: 16 kHz sample rate, 64 kbps bitrate
- **Current**: 48 kHz sample rate, 192 kbps bitrate
- **Improvement**: ~3x better frequency response, ~3x better bitrate = significantly better audio quality

## Security

- File type validation (whitelist approach)
- File size limits (10MB maximum)
- CSRF protection via Django middleware
- Anonymous contributions allowed (for community participation)
- File stored securely in `media/audio/contributions/`

## Testing Checklist

- [ ] Test recording on mobile Chrome
- [ ] Test recording on mobile Safari
- [ ] Test file upload fallback
- [ ] Test permission denial handling
- [ ] Test background upload (navigate away during upload)
- [ ] Test compression effectiveness
- [ ] Test error messages in Spanish
- [ ] Test accessibility with screen reader
- [ ] Test on low-end Android device
- [ ] Test with slow network connection

## Future Enhancements

1. Service Worker for true background uploads
2. Chunked uploads for very large files
3. Audio waveform visualization
4. Real-time audio level indicators
5. Multiple language recording in one session
6. Audio editing capabilities (trim, normalize)
