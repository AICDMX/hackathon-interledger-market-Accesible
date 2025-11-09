"""
Management command to import Otomi (?uhu) audio files from media/Audio/mp3/
and create AudioSnippet records for static UI elements.

Mapping of Spanish titles to UI elements:
- Mi Dinero - Mi Billetera -> dashboard_my_money
- Mis Productos -> dashboard_my_products  
- Mis Trabajos por terminar -> dashboard_pending_jobs
- Inicio -> dashboard_home
- Ingresar - Iniciar Sesi?n -> button_login
- Contrase?a -> form_password
- Confirma tu Contrase?a -> form_password_confirm
- Nombre de usuario -> form_username
- N?mero de tel?fono -> form_phone
- Escoge tu idioma -Qu? idiomas hablas -> form_language_selection
- No esta mi idioma - Solicitar otro idioma -> button_request_language
- Perd?n esto a?n no se ha traducido -> message_not_translated
- Comprador -> role_funder
- Los dos (contratar - vender) -> role_both
- Otomi -> language_otomi
- Crear arte sobre este tema -> button_create_art
- Crear una versi?n local -> button_create_local_version
- Crear una versi?n local de este audio -> button_create_local_audio
- Crear una versi?n local de este video -> button_create_local_video
- Adaptar esto a tus palabras locales -> button_adapt_local
- Bienvenidos a nuestra casa... -> message_welcome
- Este domingo son las elecciones... -> message_elections
- Al registrarte, aceptas... -> message_terms_acceptance
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from audio.models import AudioSnippet, StaticUIElement

# Mapping of Spanish titles (from filename) to UI element slugs
AUDIO_MAPPING = {
    'Mi-Dinero---Mi-Billetera.mp3': {
        'slug': 'dashboard_my_money',
        'label_es': 'Mi Dinero - Mi Billetera',
        'label_en': 'My Money - My Wallet',
        'category': 'dashboard',
        'target_field': 'label',
    },
    'Mis-Productos.mp3': {
        'slug': 'dashboard_my_products',
        'label_es': 'Mis Productos',
        'label_en': 'My Products',
        'category': 'dashboard',
        'target_field': 'label',
    },
    'Mis-Trabajos-por-terminar.mp3': {
        'slug': 'dashboard_pending_jobs',
        'label_es': 'Mis Trabajos por terminar',
        'label_en': 'My Pending to Finish Jobs',
        'category': 'dashboard',
        'target_field': 'label',
    },
    'Inicio.mp3': {
        'slug': 'dashboard_home',
        'label_es': 'Inicio',
        'label_en': 'Home',
        'category': 'dashboard',
        'target_field': 'label',
    },
    'Ingresar-Iniciar-Sesi?n.mp3': {
        'slug': 'button_login',
        'label_es': 'Ingresar - Iniciar Sesi?n',
        'label_en': 'Login - Sign In',
        'category': 'button',
        'target_field': 'label',
    },
    'Ingresar---Iniciar-Sesi?n.mp3': {
        'slug': 'button_login',
        'label_es': 'Ingresar - Iniciar Sesi?n',
        'label_en': 'Login - Sign In',
        'category': 'button',
        'target_field': 'label',
    },
    'Contrase?a.mp3': {
        'slug': 'form_password',
        'label_es': 'Contrase?a',
        'label_en': 'Password',
        'category': 'form',
        'target_field': 'label',
    },
    'Confirma-tu-Contrase?a.mp3': {
        'slug': 'form_password_confirm',
        'label_es': 'Confirma tu Contrase?a',
        'label_en': 'Confirm Password',
        'category': 'form',
        'target_field': 'label',
    },
    'Nombre-de-usuario.mp3': {
        'slug': 'form_username',
        'label_es': 'Nombre de usuario',
        'label_en': 'Username',
        'category': 'form',
        'target_field': 'label',
    },
    'N?mero-de-tel?fono.mp3': {
        'slug': 'form_phone',
        'label_es': 'N?mero de tel?fono',
        'label_en': 'Phone Number',
        'category': 'form',
        'target_field': 'label',
    },
    'Escoge-tu-idioma--Qu?-idiomas-hablas.mp3': {
        'slug': 'form_language_selection',
        'label_es': 'Escoge tu idioma - Qu? idiomas hablas',
        'label_en': 'Choose your language - What languages do you speak',
        'category': 'form',
        'target_field': 'label',
    },
    'No-esta-mi-idioma---Solicitar-otro-idioma.mp3': {
        'slug': 'button_request_language',
        'label_es': 'No esta mi idioma - Solicitar otro idioma',
        'label_en': 'My language is not here - Request another language',
        'category': 'button',
        'target_field': 'label',
    },
    'Perd?n-esto-a?n-no-se-ha-traducido.mp3': {
        'slug': 'message_not_translated',
        'label_es': 'Perd?n esto a?n no se ha traducido',
        'label_en': 'Sorry this has not been translated yet',
        'category': 'message',
        'target_field': 'label',
    },
    'Perdon-aun-no-hay-traduccion.mp3': {
        'slug': 'message_not_translated',
        'label_es': 'Perd?n aun no hay traduccion',
        'label_en': 'Sorry there is no translation yet',
        'category': 'message',
        'target_field': 'label',
    },
    'Comprador.mp3': {
        'slug': 'role_funder',
        'label_es': 'Comprador',
        'label_en': 'Funder',
        'category': 'other',
        'target_field': 'label',
    },
    'Los-dos-(contratar---vender).mp3': {
        'slug': 'role_both',
        'label_es': 'Los dos (contratar - vender)',
        'label_en': 'Both (hire - sell)',
        'category': 'other',
        'target_field': 'label',
    },
    'Otomi.mp3': {
        'slug': 'language_otomi',
        'label_es': 'Otomi',
        'label_en': 'Otomi',
        'category': 'other',
        'target_field': 'label',
    },
    'Crear-arte-sobre-este-tema.mp3': {
        'slug': 'button_create_art',
        'label_es': 'Crear arte sobre este tema',
        'label_en': 'Create art about this topic',
        'category': 'button',
        'target_field': 'label',
    },
    'Crear-una-versi?n-local.mp3': {
        'slug': 'button_create_local_version',
        'label_es': 'Crear una versi?n local',
        'label_en': 'Create a local version',
        'category': 'button',
        'target_field': 'label',
    },
    'Crear-una-versi?n-local-de-este-audio.mp3': {
        'slug': 'button_create_local_audio',
        'label_es': 'Crear una versi?n local de este audio',
        'label_en': 'Create a local version of this audio',
        'category': 'button',
        'target_field': 'label',
    },
    'Crear-una-versi?n-local-de-este-video.mp3': {
        'slug': 'button_create_local_video',
        'label_es': 'Crear una versi?n local de este video',
        'label_en': 'Create a local version of this video',
        'category': 'button',
        'target_field': 'label',
    },
    'Adaptar-esto-a-tus-palabras-locales.mp3': {
        'slug': 'button_adapt_local',
        'label_es': 'Adaptar esto a tus palabras locales',
        'label_en': 'Adapt this to your local words',
        'category': 'button',
        'target_field': 'label',
    },
    'Bienvenidos-a-nuestra-casa,-la-casa-del-bosque.-Cuiden-de-nuestra-tierra-como-nosotros-lo-hacemos..mp3': {
        'slug': 'message_welcome',
        'label_es': 'Bienvenidos a nuestra casa, la casa del bosque. Cuiden de nuestra tierra como nosotros lo hacemos.',
        'label_en': 'Welcome to our house, the house of the forest. Take care of our land as we do.',
        'category': 'message',
        'target_field': 'label',
    },
    'Este-domingo-son-las-elecciones.-Tu-voto-es-libre-y-secreto.-Participa-para-decidir-el-futuro-de-tu-comunidad.-Acude-a-tu-casilla-con-tu-credencial.-Tu-voz-cuenta.mp3': {
        'slug': 'message_elections',
        'label_es': 'Este domingo son las elecciones. Tu voto es libre y secreto. Participa para decidir el futuro de tu comunidad. Acude a tu casilla con tu credencial. Tu voz cuenta.',
        'label_en': 'This Sunday are the elections. Your vote is free and secret. Participate to decide the future of your community. Go to your polling station with your credential. Your voice counts.',
        'category': 'message',
        'target_field': 'label',
    },
    'Al-registrarte,-aceptas-nuestros-T?rminos-y-Condiciones-y-nuestra-Pol?tica-de-Privacidad.mp3': {
        'slug': 'message_terms_acceptance',
        'label_es': 'Al registrarte, aceptas nuestros T?rminos y Condiciones y nuestra Pol?tica de Privacidad.',
        'label_en': 'By registering, you accept our Terms and Conditions and our Privacy Policy.',
        'category': 'message',
        'target_field': 'label',
    },
}


class Command(BaseCommand):
    help = 'Import Otomi (?uhu) audio files from media/Audio/mp3/ and create AudioSnippet records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--audio-dir',
            type=str,
            default='media/Audio/mp3',
            help='Directory containing the MP3 audio files'
        )
        parser.add_argument(
            '--language-code',
            type=str,
            default='oto',
            help='Language code for the audio files (default: oto for Otomi)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )

    def handle(self, *args, **options):
        audio_dir = Path(options['audio_dir'])
        language_code = options['language_code']
        dry_run = options['dry_run']

        # If relative path, make it relative to project root
        if not audio_dir.is_absolute():
            # Assume we're in marketplace-py directory, go up one level for media/
            project_root = Path(__file__).parent.parent.parent.parent.parent
            audio_dir = project_root / audio_dir

        if not audio_dir.exists():
            self.stdout.write(self.style.ERROR(f'Directory {audio_dir} does not exist'))
            return

        # Get or create ContentType for StaticUIElement
        try:
            content_type = ContentType.objects.get(app_label='audio', model='staticuielement')
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.WARNING('StaticUIElement model not found. Creating migration first...'))
            self.stdout.write(self.style.ERROR('Please run: python manage.py makemigrations && python manage.py migrate'))
            return

        imported_count = 0
        skipped_count = 0
        error_count = 0

        # Process each MP3 file
        for mp3_file in sorted(audio_dir.glob('*.mp3')):
            filename = mp3_file.name
            
            if filename not in AUDIO_MAPPING:
                self.stdout.write(self.style.WARNING(f'Skipping {filename} - no mapping found'))
                skipped_count += 1
                continue

            mapping = AUDIO_MAPPING[filename]
            slug = mapping['slug']

            try:
                # Get or create StaticUIElement
                ui_element, created = StaticUIElement.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'label_es': mapping['label_es'],
                        'label_en': mapping.get('label_en', ''),
                        'category': mapping['category'],
                        'description': f'Audio file: {filename}',
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created UI element: {slug}'))
                else:
                    # Update if exists
                    ui_element.label_es = mapping['label_es']
                    if mapping.get('label_en'):
                        ui_element.label_en = mapping['label_en']
                    ui_element.category = mapping['category']
                    ui_element.save()

                # Check if AudioSnippet already exists
                existing = AudioSnippet.objects.filter(
                    content_type=content_type,
                    object_id=ui_element.pk,
                    target_field=mapping['target_field'],
                    language_code=language_code
                ).first()

                if existing:
                    if dry_run:
                        self.stdout.write(f'Would skip {filename} - AudioSnippet already exists')
                    else:
                        self.stdout.write(self.style.WARNING(f'Skipping {filename} - AudioSnippet already exists'))
                    skipped_count += 1
                    continue

                if dry_run:
                    self.stdout.write(f'Would import {filename} -> {slug} ({language_code})')
                    imported_count += 1
                    continue

                # Create AudioSnippet
                with open(mp3_file, 'rb') as f:
                    audio_file = File(f, name=mp3_file.name)
                    audio_snippet = AudioSnippet.objects.create(
                        content_type=content_type,
                        object_id=ui_element.pk,
                        target_field=mapping['target_field'],
                        language_code=language_code,
                        transcript=mapping['label_es'],  # Use Spanish label as transcript
                        status='ready',
                        file=audio_file,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Imported {filename} -> {slug}'))
                    imported_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {filename}: {str(e)}'))
                error_count += 1

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Imported: {imported_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
