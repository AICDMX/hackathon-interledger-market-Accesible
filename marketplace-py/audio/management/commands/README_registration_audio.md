# Registration Button Audio Setup

This document explains how to set up audio for the registration buttons:
- **Register as Job Creator** ? Audio: "Quiero contratar"
- **Register as Job Doer** ? Audio: "Quiero ofrecer mis servicios"

## Audio Files Required

Place the following audio files in `media/Audio/mp3/`:

1. **Quiero-contratar.mp3** - For "Register as Job Creator" button
2. **Quiero-ofrecer-mis-servicios.mp3** - For "Register as Job Doer" button

## Setup Steps

1. **Ensure audio files are in place:**
   ```bash
   # Audio files should be in:
   media/Audio/mp3/Quiero-contratar.mp3
   media/Audio/mp3/Quiero-ofrecer-mis-servicios.mp3
   ```

2. **Run the management command:**
   ```bash
   cd marketplace-py
   uv run python manage.py setup_registration_audio
   ```

3. **Dry run (to preview changes):**
   ```bash
   uv run python manage.py setup_registration_audio --dry-run
   ```

4. **If audio files are not ready yet, create StaticUIElement entries first:**
   ```bash
   uv run python manage.py setup_registration_audio --skip-audio-file
   ```
   Then add audio files later and run the command again without `--skip-audio-file`.

## What the Command Does

The `setup_registration_audio` management command will:

1. Create `StaticUIElement` entries for:
   - `button_register_job_creator` (Spanish: "Registrarse como Creador de Trabajos")
   - `button_register_job_doer` (Spanish: "Registrarse como Realizador de Trabajos")

2. Create `AudioSnippet` entries linking the audio files to these UI elements

3. Set the language code to `es` (Spanish) by default

## Where Audio Players Appear

Audio players will appear next to:
- The "Register as Job Creator" button on `/users/register_creator/`
- The "Register as Job Doer" button on `/users/register_doer/`
- The "Register as Job Creator" link on `/users/login/`
- The "Register as Job Doer" link on `/users/login/`

## Customization

You can customize the command with these options:

- `--audio-dir PATH`: Specify a different directory for audio files (default: `media/Audio/mp3`)
- `--language-code CODE`: Use a different language code (default: `es`)
- `--dry-run`: Preview changes without making them
- `--skip-audio-file`: Create StaticUIElement entries without requiring audio files

## Troubleshooting

If audio files are missing:
- The command will warn you and skip those entries
- Use `--skip-audio-file` to create the UI elements first, then add files and run again

If StaticUIElement entries already exist:
- The command will update them with the latest labels and categories
- AudioSnippet entries will be updated with new audio files if they exist
