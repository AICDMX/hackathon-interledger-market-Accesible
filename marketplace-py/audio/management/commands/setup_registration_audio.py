"""
Management command to set up audio for registration buttons:
- Register as Job Creator -> "Quiero contratar"
- Register as Job Doer -> "Quiero ofrecer mis servicios"

This command creates StaticUIElement entries and AudioSnippet entries for Spanish audio.
The audio files should be placed in media/Audio/mp3/ with these names:
- Quiero-contratar.mp3
- Quiero-ofrecer-mis-servicios.mp3
"""
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from audio.models import AudioSnippet, StaticUIElement


# Mapping of slugs to their configuration
REGISTRATION_AUDIO_MAPPING = {
    'button_register_job_creator': {
        'label_es': 'Registrarse como Creador de Trabajos',
        'label_en': 'Register as Job Creator',
        'category': 'button',
        'audio_filename': 'Quiero-contratar.mp3',
        'transcript': 'Quiero contratar',
    },
    'button_register_job_doer': {
        'label_es': 'Registrarse como Realizador de Trabajos',
        'label_en': 'Register as Job Doer',
        'category': 'button',
        'audio_filename': 'Quiero-ofrecer-mis-servicios.mp3',
        'transcript': 'Quiero ofrecer mis servicios',
    },
}


class Command(BaseCommand):
    help = 'Set up audio for registration buttons (Quiero contratar and Quiero ofrecer mis servicios)'

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
            default='es',
            help='Language code for the audio files (default: es for Spanish)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--skip-audio-file',
            action='store_true',
            help='Create StaticUIElement entries without requiring audio files (for testing)',
        )

    def handle(self, *args, **options):
        audio_dir = Path(options['audio_dir'])
        language_code = options['language_code']
        dry_run = options['dry_run']
        skip_audio_file = options['skip_audio_file']

        # If relative path, make it relative to project root
        if not audio_dir.is_absolute():
            # Assume we're in marketplace-py directory, go up one level for media/
            project_root = Path(__file__).parent.parent.parent.parent.parent
            audio_dir = project_root / audio_dir

        if not audio_dir.exists() and not skip_audio_file:
            self.stdout.write(self.style.WARNING(f'Directory {audio_dir} does not exist'))
            self.stdout.write(self.style.WARNING('Use --skip-audio-file to create StaticUIElement entries without audio files'))
            return

        # Get ContentType for StaticUIElement
        try:
            content_type = ContentType.objects.get(app_label='audio', model='staticuielement')
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR('StaticUIElement model not found. Please run migrations first.'))
            return

        created_ui_count = 0
        updated_ui_count = 0
        created_audio_count = 0
        updated_audio_count = 0
        skipped_count = 0
        error_count = 0

        # Process each registration button
        for slug, config in REGISTRATION_AUDIO_MAPPING.items():
            audio_filename = config['audio_filename']
            audio_file_path = audio_dir / audio_filename

            # Check if audio file exists (unless skipping)
            if not skip_audio_file and not audio_file_path.exists():
                self.stdout.write(
                    self.style.WARNING(f'Audio file not found: {audio_file_path}')
                )
                self.stdout.write(
                    self.style.WARNING(f'  Expected file: {audio_filename}')
                )
                if not dry_run:
                    skipped_count += 1
                continue

            try:
                # Get or create StaticUIElement
                ui_element, ui_created = StaticUIElement.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'label_es': config['label_es'],
                        'label_en': config['label_en'],
                        'category': config['category'],
                        'description': f'Registration button: {config["label_en"]}',
                    }
                )

                if ui_created:
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would create UI element: {slug}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Created UI element: {slug}'))
                    created_ui_count += 1
                else:
                    # Update if exists
                    if not dry_run:
                        ui_element.label_es = config['label_es']
                        ui_element.label_en = config['label_en']
                        ui_element.category = config['category']
                        ui_element.save()
                        self.stdout.write(self.style.SUCCESS(f'Updated UI element: {slug}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would update UI element: {slug}'))
                    updated_ui_count += 1

                # Create or update AudioSnippet
                if skip_audio_file:
                    # Create entry without audio file (for testing)
                    audio_snippet, audio_created = AudioSnippet.objects.get_or_create(
                        content_type=content_type,
                        object_id=ui_element.pk,
                        target_field='label',
                        language_code=language_code,
                        defaults={
                            'transcript': config['transcript'],
                            'status': 'draft',
                        }
                    )
                    if audio_created:
                        if dry_run:
                            self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would create AudioSnippet (no file): {slug}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Created AudioSnippet (no file): {slug}'))
                        created_audio_count += 1
                    else:
                        if not dry_run:
                            audio_snippet.transcript = config['transcript']
                            audio_snippet.save()
                            self.stdout.write(self.style.SUCCESS(f'Updated AudioSnippet (no file): {slug}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would update AudioSnippet (no file): {slug}'))
                        updated_audio_count += 1
                else:
                    # Check if AudioSnippet already exists
                    existing = AudioSnippet.objects.filter(
                        content_type=content_type,
                        object_id=ui_element.pk,
                        target_field='label',
                        language_code=language_code
                    ).first()

                    if existing:
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f'[DRY RUN] AudioSnippet already exists: {slug} ({language_code})'))
                        else:
                            # Update existing audio snippet with new file
                            with open(audio_file_path, 'rb') as f:
                                existing.file.save(audio_filename, File(f), save=True)
                            existing.transcript = config['transcript']
                            existing.status = 'ready'
                            existing.save()
                            self.stdout.write(self.style.SUCCESS(f'Updated AudioSnippet: {slug}'))
                        updated_audio_count += 1
                    else:
                        if dry_run:
                            self.stdout.write(self.style.SUCCESS(f'[DRY RUN] Would create AudioSnippet: {slug}'))
                        else:
                            # Create new audio snippet
                            with open(audio_file_path, 'rb') as f:
                                audio_snippet = AudioSnippet.objects.create(
                                    content_type=content_type,
                                    object_id=ui_element.pk,
                                    target_field='label',
                                    language_code=language_code,
                                    transcript=config['transcript'],
                                    status='ready',
                                    file=File(f, name=audio_filename)
                                )
                            self.stdout.write(self.style.SUCCESS(f'Created AudioSnippet: {slug}'))
                        created_audio_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Error processing {slug}: {str(e)}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.SUCCESS('DRY RUN SUMMARY'))
        else:
            self.stdout.write(self.style.SUCCESS('SETUP SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'StaticUIElement created: {created_ui_count}')
        self.stdout.write(f'StaticUIElement updated: {updated_ui_count}')
        self.stdout.write(f'AudioSnippet created: {created_audio_count}')
        self.stdout.write(f'AudioSnippet updated: {updated_audio_count}')
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (missing files): {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

        if skip_audio_file:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Note: Audio files were skipped. To add audio files:'))
            self.stdout.write(self.style.WARNING('  1. Place audio files in media/Audio/mp3/'))
            self.stdout.write(self.style.WARNING('  2. Run this command again without --skip-audio-file'))
