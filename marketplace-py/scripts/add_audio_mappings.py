#!/usr/bin/env python
"""
Script to add audio mappings for front-end buttons.
Matches existing audio files in /media/Audio/ to StaticUIElement objects.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')
django.setup()

from audio.models import StaticUIElement, AudioSnippet
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from pathlib import Path

# Base path for audio files
AUDIO_BASE_PATH = Path(__file__).parent.parent.parent / 'media' / 'Audio'
AUDIO_MP3_PATH = AUDIO_BASE_PATH / 'mp3'

# Mapping of audio filenames (without extension) to their purpose
# Format: filename_stem -> (label_es, label_en, category, slug_prefix)
AUDIO_FILE_MAPPINGS = {
    # Navigation and main actions
    'Inicio': ('Inicio', 'Home', 'navigation', 'nav_home'),
    'Ingresar-Iniciar-Sesi?n': ('Ingresar / Iniciar Sesi?n', 'Login', 'navigation', 'nav_login'),
    'Ingresar---Iniciar-Sesi?n': ('Ingresar / Iniciar Sesi?n', 'Login', 'navigation', 'nav_login_alt'),
    
    # Dashboard items
    'Mi-Dinero---Mi-Billetera': ('Mi Dinero / Mi Billetera', 'My Money / My Wallet', 'dashboard', 'my_money'),
    'Mis-Productos': ('Mis Productos', 'My Products', 'dashboard', 'my_products'),
    'Mis-Trabajos-por-terminar': ('Mis Trabajos por terminar', 'My Pending Jobs', 'dashboard', 'pending_jobs'),
    
    # User registration/profile
    'Comprador': ('Comprador', 'Buyer', 'form', 'label_buyer'),
    'Nombre-de-usuario': ('Nombre de usuario', 'Username', 'form', 'label_username'),
    'Contrase?a': ('Contrase?a', 'Password', 'form', 'label_password'),
    'Confirma-tu-Contrase?a': ('Confirma tu Contrase?a', 'Confirm Password', 'form', 'label_confirm_password'),
    'N?mero-de-tel?fono': ('N?mero de tel?fono', 'Phone Number', 'form', 'label_phone'),
    'Los-dos-(contratar---vender)': ('Los dos (contratar / vender)', 'Both (hire / sell)', 'form', 'label_both_roles'),
    
    # Language selection
    'Escoge-tu-idioma--Qu?-idiomas-hablas': ('Escoge tu idioma / Qu? idiomas hablas', 'Choose your language / What languages do you speak', 'form', 'label_select_language'),
    'Otomi': ('Otom?', 'Otomi', 'other', 'language_otomi'),
    'No-esta-mi-idioma---Solicitar-otro-idioma': ('No est? mi idioma / Solicitar otro idioma', 'My language is not here / Request another language', 'form', 'label_request_language'),
    
    # Job creation
    'Crear-arte-sobre-este-tema': ('Crear arte sobre este tema', 'Create art about this theme', 'other', 'job_create_art'),
    'Crear-una-versi?n-local': ('Crear una versi?n local', 'Create a local version', 'other', 'job_create_local_version'),
    'Crear-una-versi?n-local-de-este-audio': ('Crear una versi?n local de este audio', 'Create a local version of this audio', 'other', 'job_create_local_audio'),
    'Crear-una-versi?n-local-de-este-video': ('Crear una versi?n local de este video', 'Create a local version of this video', 'other', 'job_create_local_video'),
    
    # Messages
    'Perd?n-esto-a?n-no-se-ha-traducido': ('Perd?n esto a?n no se ha traducido', 'Sorry this has not been translated yet', 'message', 'message_not_translated'),
    'Perdon-aun-no-hay-traduccion': ('Perd?n a?n no hay traducci?n', 'Sorry there is no translation yet', 'message', 'message_no_translation'),
    'Adaptar-esto-a-tus-palabras-locales': ('Adaptar esto a tus palabras locales', 'Adapt this to your local words', 'message', 'message_adapt_local'),
    
    # Legal/Terms
    'Al-registrarte,-aceptas-nuestros-T?rminos-y-Condiciones-y-nuestra-Pol?tica-de-Privacidad': 
        ('Al registrarte, aceptas nuestros T?rminos y Condiciones y nuestra Pol?tica de Privacidad', 
         'By registering, you accept our Terms and Conditions and our Privacy Policy', 
         'message', 'message_terms_acceptance'),
    
    # Example community message
    'Bienvenidos-a-nuestra-casa,-la-casa-del-bosque.-Cuiden-de-nuestra-tierra-como-nosotros-lo-hacemos.':
        ('Bienvenidos a nuestra casa, la casa del bosque. Cuiden de nuestra tierra como nosotros lo hacemos.',
         'Welcome to our home, the home of the forest. Take care of our land as we do.',
         'message', 'message_welcome_forest'),
    
    # Voting message example
    'Este-domingo-son-las-elecciones.-Tu-voto-es-libre-y-secreto.-Participa-para-decidir-el-futuro-de-tu-comunidad.-Acude-a-tu-casilla-con-tu-credencial.-Tu-voz-cuenta':
        ('Este domingo son las elecciones. Tu voto es libre y secreto. Participa para decidir el futuro de tu comunidad. Acude a tu casilla con tu credencial. Tu voz cuenta.',
         'This Sunday are the elections. Your vote is free and secret. Participate to decide the future of your community. Go to your polling station with your credential. Your voice counts.',
         'message', 'message_voting'),
}

# Additional mappings for navigation buttons found in templates
NAV_BUTTON_MAPPINGS = {
    'nav_browse_jobs': ('Buscar trabajos', 'Browse Jobs', 'navigation'),
    'nav_create_job': ('Crear trabajo', 'Create Job', 'navigation'),
    'nav_my_jobs': ('Mis trabajos', 'My Jobs', 'navigation'),
    'nav_my_jobs_creator': ('Mis trabajos', 'My Jobs', 'navigation'),
    'nav_profile': ('Perfil', 'Profile', 'navigation'),
    'nav_logout': ('Cerrar sesi?n', 'Logout', 'navigation'),
    'nav_register_creator': ('Registrarse como creador', 'Register as Creator', 'navigation'),
    'nav_register_doer': ('Registrarse como trabajador', 'Register as Doer', 'navigation'),
}

# Button action mappings found in templates
BUTTON_ACTION_MAPPINGS = {
    'button_update_profile': ('Actualizar perfil', 'Update Profile', 'button'),
    'button_change_password': ('Cambiar contrase?a', 'Change Password', 'button'),
    'button_view_details': ('Ver detalles', 'View Details', 'button'),
    'button_edit_draft': ('Editar borrador', 'Edit Draft', 'button'),
    'button_duplicate_job': ('Duplicar trabajo', 'Duplicate Job', 'button'),
    'button_accept': ('Aceptar', 'Accept', 'button'),
    'button_decline': ('Rechazar', 'Decline', 'button'),
    'button_approve': ('Aprobar', 'Approve', 'button'),
    'button_reject': ('Rechazar', 'Reject', 'button'),
    'button_reset_to_pending': ('Restablecer a pendiente', 'Reset to Pending', 'button'),
    'button_start_contract': ('Iniciar contrato', 'Start Contract', 'button'),
    'button_cancel_contract': ('Cancelar contrato', 'Cancel Contract', 'button'),
    'button_complete_contract': ('Completar contrato', 'Complete Contract', 'button'),
    'button_submit_work_for_job': ('Enviar trabajo para este trabajo', 'Submit Work for This Job', 'button'),
    'button_apply_to_job': ('Aplicar a este trabajo', 'Apply to This Job', 'button'),
    'button_save_draft': ('Guardar como borrador', 'Save as Draft', 'button'),
    'button_create_job': ('Crear trabajo', 'Create Job', 'button'),
    'button_login': ('Iniciar sesi?n', 'Login', 'button'),
    'button_register_job_creator': ('Registrarse como creador de trabajos', 'Register as Job Creator', 'button'),
    'button_register_job_doer': ('Registrarse como trabajador', 'Register as Job Doer', 'button'),
    'button_preview': ('Vista previa', 'Preview', 'button'),
    'button_view_public_page': ('Ver p?gina p?blica', 'View Public Page', 'button'),
    'button_edit': ('Editar', 'Edit', 'button'),
}

# Label mappings found in templates
LABEL_MAPPINGS = {
    'label_total_earned': ('Total ganado', 'Total Earned', 'form'),
    'label_total_spent': ('Total gastado', 'Total Spent', 'form'),
    'label_balance': ('Balance', 'Balance', 'form'),
}

# Message mappings
MESSAGE_MAPPINGS = {
    'message_already_submitted': ('Ya enviaste trabajo para este trabajo. Solo puedes enviar una vez por trabajo.', 
                                  'You have already submitted work for this job. You can only submit once per job.', 
                                  'message'),
}


def create_static_ui_elements():
    """Create StaticUIElement entries for all mappings."""
    print("Creating StaticUIElement entries...")
    created_count = 0
    updated_count = 0
    
    # Combine all mappings
    all_mappings = {}
    
    # From audio files
    for filename, (label_es, label_en, category, slug) in AUDIO_FILE_MAPPINGS.items():
        all_mappings[slug] = (label_es, label_en, category, filename)
    
    # From template references (no audio file yet)
    for slug, (label_es, label_en, category) in NAV_BUTTON_MAPPINGS.items():
        if slug not in all_mappings:
            all_mappings[slug] = (label_es, label_en, category, None)
    
    for slug, (label_es, label_en, category) in BUTTON_ACTION_MAPPINGS.items():
        if slug not in all_mappings:
            all_mappings[slug] = (label_es, label_en, category, None)
    
    for slug, (label_es, label_en, category) in LABEL_MAPPINGS.items():
        if slug not in all_mappings:
            all_mappings[slug] = (label_es, label_en, category, None)
    
    for slug, (label_es, label_en, category) in MESSAGE_MAPPINGS.items():
        if slug not in all_mappings:
            all_mappings[slug] = (label_es, label_en, category, None)
    
    # Create or update elements
    for slug, (label_es, label_en, category, filename) in all_mappings.items():
        element, created = StaticUIElement.objects.get_or_create(
            slug=slug,
            defaults={
                'label_es': label_es,
                'label_en': label_en,
                'category': category,
                'description': f'Audio file: {filename}' if filename else 'No audio file yet',
            }
        )
        
        if created:
            print(f"  ? Created: {slug} ({label_es})")
            created_count += 1
        else:
            # Update existing
            element.label_es = label_es
            element.label_en = label_en
            element.category = category
            if filename:
                element.description = f'Audio file: {filename}'
            element.save()
            print(f"  ? Updated: {slug} ({label_es})")
            updated_count += 1
    
    print(f"\nCreated {created_count} new elements, updated {updated_count} existing elements.")
    return all_mappings


def add_audio_snippets(all_mappings):
    """Add AudioSnippet entries linking audio files to StaticUIElements."""
    print("\nAdding audio snippets...")
    content_type = ContentType.objects.get_for_model(StaticUIElement)
    added_count = 0
    skipped_count = 0
    
    for slug, (label_es, label_en, category, filename) in all_mappings.items():
        if not filename:
            continue
        
        # Get the StaticUIElement
        try:
            ui_element = StaticUIElement.objects.get(slug=slug)
        except StaticUIElement.DoesNotExist:
            print(f"  ? Element not found: {slug}")
            continue
        
        # Find the audio file
        audio_file_mp3 = AUDIO_MP3_PATH / f'{filename}.mp3'
        audio_file_opus = AUDIO_BASE_PATH / f'{filename}.opus'
        
        # Prefer MP3 for wider compatibility
        audio_file = audio_file_mp3 if audio_file_mp3.exists() else audio_file_opus
        
        if not audio_file.exists():
            print(f"  ? Audio file not found: {filename}")
            continue
        
        # Check if snippet already exists for Spanish
        existing_snippet = AudioSnippet.objects.filter(
            content_type=content_type,
            object_id=ui_element.pk,
            target_field='label',
            language_code='es'
        ).first()
        
        if existing_snippet:
            print(f"  - Skipped (exists): {slug} (es)")
            skipped_count += 1
            continue
        
        # Create AudioSnippet
        try:
            with open(audio_file, 'rb') as f:
                snippet = AudioSnippet.objects.create(
                    content_type=content_type,
                    object_id=ui_element.pk,
                    target_field='label',
                    language_code='es',
                    transcript=label_es,
                    status='ready',
                )
                snippet.file.save(audio_file.name, File(f), save=True)
                print(f"  ? Added audio: {slug} (es) - {audio_file.name}")
                added_count += 1
        except Exception as e:
            print(f"  ? Error adding audio for {slug}: {e}")
    
    print(f"\nAdded {added_count} audio snippets, skipped {skipped_count} existing snippets.")


def main():
    print("=" * 60)
    print("Adding Audio Mappings for Front-End Buttons")
    print("=" * 60)
    
    # Step 1: Create StaticUIElement entries
    all_mappings = create_static_ui_elements()
    
    # Step 2: Add audio snippets
    add_audio_snippets(all_mappings)
    
    print("\n" + "=" * 60)
    print("Done! Audio mappings have been added.")
    print("=" * 60)


if __name__ == '__main__':
    main()
