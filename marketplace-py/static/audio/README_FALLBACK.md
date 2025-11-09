# Fallback Audio File

## Overview
The fallback audio file is played when:
- A specific audio snippet is not available
- The audio file fails to load
- There's a network error

## File Format
**Recommended format: MP3**

MP3 is the best choice because:
- Widest browser support (all modern browsers)
- Good compression (small file size)
- Works well for short messages

## File Location
Place the fallback audio file at:
```
static/audio/fallback.mp3
```

This path is configured in `settings.py` as `AUDIO_FALLBACK_FILE = 'audio/fallback.mp3'`

## File Specifications
- **Format**: MP3 (`.mp3` extension)
- **Recommended duration**: 1-3 seconds
- **Recommended size**: Under 50KB for fast loading
- **Sample rate**: 44.1 kHz or 48 kHz
- **Bitrate**: 64-128 kbps (good balance of quality and file size)

## Content Suggestions
The fallback audio can be:
1. **A simple beep/tone** - Quick, neutral sound
2. **A spoken message** - "Audio not available" or "Please wait"
3. **Silence** - Minimal file size, just indicates audio system is working
4. **A gentle chime** - User-friendly notification sound

## Creating the File

### Option 1: Using Online Tools
1. Use a text-to-speech service (e.g., Google TTS, Amazon Polly)
2. Record a short message: "Audio not available"
3. Export as MP3

### Option 2: Using Audio Editing Software
1. Use Audacity (free, open-source)
2. Record or generate a short audio clip
3. Export as MP3 with these settings:
   - Format: MP3
   - Bitrate: 128 kbps
   - Sample rate: 44.1 kHz
   - Channels: Mono (smaller file size)

### Option 3: Using Command Line (FFmpeg)
```bash
# Create a simple beep tone (1 second, 440Hz)
ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -acodec libmp3lame -b:a 128k static/audio/fallback.mp3

# Or convert an existing audio file
ffmpeg -i input.wav -acodec libmp3lame -b:a 128k static/audio/fallback.mp3
```

### Option 4: Download a Free Sound Effect
- Visit freesound.org or similar sites
- Search for "notification", "beep", or "chime"
- Download and convert to MP3 if needed
- Place in `static/audio/fallback.mp3`

## Testing
After adding the file:
1. Run `python manage.py collectstatic` (if using STATIC_ROOT)
2. Test by clicking an audio button for content without audio
3. The fallback should play instead of showing an error

## Customization
To change the fallback file path, update `settings.py`:
```python
AUDIO_FALLBACK_FILE = 'audio/your-custom-fallback.mp3'
```

Make sure the file exists in the `static/audio/` directory.
