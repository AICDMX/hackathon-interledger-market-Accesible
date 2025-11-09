# Otomi (?uhu) Audio Import - Implementation Summary

## Completed Tasks

1. ? **Added Otomi (?uhu) language support**
   - Updated `LANGUAGES` in `settings.py` to show "Otomi (?uhu)" instead of just "Otomi"
   - Updated language choices in `users/forms.py`
   - Language code remains `oto` (as it was already in use)

2. ? **Created StaticUIElement model**
   - Added to `audio/models.py`
   - Represents static UI elements (dashboard items, form labels, buttons, etc.)
   - Fields: slug, label_es, label_en, category, description
   - Categories: dashboard, form, button, navigation, message, other

3. ? **Created management command**
   - `import_otomi_audio.py` in `audio/management/commands/`
   - Maps Spanish audio filenames to UI element slugs
   - Creates StaticUIElement records if they don't exist
   - Creates AudioSnippet records linked to StaticUIElement via ContentType
   - Supports dry-run mode

4. ? **Added helper function**
   - `get_audio_for_static_ui()` in `audio/mixins.py`
   - Gets audio for static UI elements by slug
   - Supports language fallback chain

5. ? **Updated admin**
   - Added StaticUIElementAdmin to `audio/admin.py`

## Audio File Mappings

The following mappings are defined in the management command:

### Dashboard Items
- `Mi-Dinero---Mi-Billetera.mp3` ? `dashboard_my_money`
- `Mis-Productos.mp3` ? `dashboard_my_products`
- `Mis-Trabajos-por-terminar.mp3` ? `dashboard_pending_jobs`
- `Inicio.mp3` ? `dashboard_home`

### Form Fields
- `Contrase?a.mp3` ? `form_password`
- `Confirma-tu-Contrase?a.mp3` ? `form_password_confirm`
- `Nombre-de-usuario.mp3` ? `form_username`
- `N?mero-de-tel?fono.mp3` ? `form_phone`
- `Escoge-tu-idioma--Qu?-idiomas-hablas.mp3` ? `form_language_selection`

### Buttons
- `Ingresar-Iniciar-Sesi?n.mp3` ? `button_login`
- `No-esta-mi-idioma---Solicitar-otro-idioma.mp3` ? `button_request_language`
- `Crear-arte-sobre-este-tema.mp3` ? `button_create_art`
- `Crear-una-versi?n-local.mp3` ? `button_create_local_version`
- `Crear-una-versi?n-local-de-este-audio.mp3` ? `button_create_local_audio`
- `Crear-una-versi?n-local-de-este-video.mp3` ? `button_create_local_video`
- `Adaptar-esto-a-tus-palabras-locales.mp3` ? `button_adapt_local`

### Messages
- `Perd?n-esto-a?n-no-se-ha-traducido.mp3` ? `message_not_translated`
- `Bienvenidos-a-nuestra-casa...mp3` ? `message_welcome`
- `Este-domingo-son-las-elecciones...mp3` ? `message_elections`
- `Al-registrarte,-aceptas...mp3` ? `message_terms_acceptance`

### Other
- `Comprador.mp3` ? `role_funder`
- `Los-dos-(contratar---vender).mp3` ? `role_both`
- `Otomi.mp3` ? `language_otomi`

## Next Steps

1. **Create migration**
   ```bash
   cd marketplace-py
   uv run python manage.py makemigrations audio
   uv run python manage.py migrate
   ```

2. **Run import command**
   ```bash
   uv run python manage.py import_otomi_audio --dry-run  # Test first
   uv run python manage.py import_otomi_audio  # Actually import
   ```

3. **Update templates to use static UI audio**
   - Create a template tag for static UI audio
   - Update dashboard.html to use audio for dashboard items
   - Update form templates to use audio for form labels
   - Update button templates to use audio for buttons

4. **Update audio_player template tag**
   - Add support for static UI elements via slug
   - Or create a separate template tag for static UI audio

## Notes

- All audio files are in Otomi (?uhu) language (language code: `oto`)
- Spanish is the written language - these audio files are for audio playback only
- The system uses ContentType to link AudioSnippet to StaticUIElement
- Language fallback chain: preferred language ? fallback language ? default language
