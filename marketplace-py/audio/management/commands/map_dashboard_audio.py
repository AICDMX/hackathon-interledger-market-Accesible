"""
Management command to map MP3 files to dashboard pictographs.

Mappings:
- Job posts -> "Trabajos contratando - Buscar Trabajos"
- My jobs dashboard -> "Mis Trabajos por terminar"
- My products -> "Trabajos contratando - Buscar Trabajos"
- My money -> "Mi Dinero - Mi Billetera"
"""
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from audio.models import AudioSnippet, StaticUIElement


# Dashboard pictograph mappings
DASHBOARD_MAPPINGS = {
    'job_post': {
        'slug_candidates': ['job_post', 'dashboard_job_post'],
        'label_es': 'Trabajos contratando - Buscar Trabajos',
        'label_en': 'Job Posts - Search Jobs',
        'mp3_filename': None,  # No MP3 file exists yet for this
        'category': 'dashboard',
    },
    'pending_jobs': {
        'slug_candidates': ['pending_jobs', 'dashboard_pending_jobs'],
        'label_es': 'Mis Trabajos por terminar',
        'label_en': 'My Pending to Finish Jobs',
        'mp3_filename': 'Mis-Trabajos-por-terminar.mp3',
        'category': 'dashboard',
    },
    'my_products': {
        'slug_candidates': ['my_products', 'dashboard_my_products'],
        'label_es': 'Trabajos contratando - Buscar Trabajos',
        'label_en': 'My Products',
        'mp3_filename': 'Mis-Productos.mp3',  # Using existing MP3 but updating label
        'category': 'dashboard',
    },
    'my_money': {
        'slug_candidates': ['my_money', 'dashboard_my_money'],
        'label_es': 'Mi Dinero - Mi Billetera',
        'label_en': 'My Money - My Wallet',
        'mp3_filename': 'Mi-Dinero---Mi-Billetera.mp3',
        'category': 'dashboard',
    },
}


class Command(BaseCommand):
    help = 'Map MP3 files to dashboard pictographs with Spanish labels'

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
            help='Show what would be mapped without actually mapping'
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

        # Get ContentType for StaticUIElement
        try:
            content_type = ContentType.objects.get(app_label='audio', model='staticuielement')
        except ContentType.DoesNotExist:
            self.stdout.write(self.style.ERROR('StaticUIElement model not found. Please run migrations first.'))
            return

        updated_count = 0
        created_count = 0
        audio_mapped_count = 0
        skipped_count = 0
        error_count = 0

        # Process each dashboard mapping
        for key, mapping in DASHBOARD_MAPPINGS.items():
            try:
                # Find existing StaticUIElement by trying slug candidates
                ui_element = None
                used_slug = None
                
                for slug_candidate in mapping['slug_candidates']:
                    try:
                        ui_element = StaticUIElement.objects.get(slug=slug_candidate)
                        used_slug = slug_candidate
                        break
                    except StaticUIElement.DoesNotExist:
                        continue

                # Create if doesn't exist
                if ui_element is None:
                    used_slug = mapping['slug_candidates'][0]  # Use first candidate
                    if dry_run:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Would create UI element: {used_slug} '
                                f'({mapping["label_es"]})'
                            )
                        )
                    else:
                        ui_element = StaticUIElement.objects.create(
                            slug=used_slug,
                            label_es=mapping['label_es'],
                            label_en=mapping['label_en'],
                            category=mapping['category'],
                            description=f'Dashboard pictograph: {key}',
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Created UI element: {used_slug} ({mapping["label_es"]})'
                            )
                        )
                        created_count += 1
                else:
                    # Update labels if they differ
                    updated = False
                    if ui_element.label_es != mapping['label_es']:
                        if dry_run:
                            self.stdout.write(
                                f'Would update {used_slug} label_es: '
                                f'"{ui_element.label_es}" -> "{mapping["label_es"]}"'
                            )
                        else:
                            ui_element.label_es = mapping['label_es']
                            updated = True
                    
                    if ui_element.label_en != mapping['label_en']:
                        if dry_run:
                            self.stdout.write(
                                f'Would update {used_slug} label_en: '
                                f'"{ui_element.label_en}" -> "{mapping["label_en"]}"'
                            )
                        else:
                            ui_element.label_en = mapping['label_en']
                            updated = True
                    
                    if ui_element.category != mapping['category']:
                        if dry_run:
                            self.stdout.write(
                                f'Would update {used_slug} category: '
                                f'"{ui_element.category}" -> "{mapping["category"]}"'
                            )
                        else:
                            ui_element.category = mapping['category']
                            updated = True
                    
                    if updated and not dry_run:
                        ui_element.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated UI element: {used_slug} ({mapping["label_es"]})'
                            )
                        )
                        updated_count += 1

                # Map MP3 file if specified
                if mapping['mp3_filename']:
                    mp3_file = audio_dir / mapping['mp3_filename']
                    
                    if not mp3_file.exists():
                        self.stdout.write(
                            self.style.WARNING(
                                f'MP3 file not found: {mp3_file} (for {key})'
                            )
                        )
                        skipped_count += 1
                        continue

                    # Check if AudioSnippet already exists
                    existing = AudioSnippet.objects.filter(
                        content_type=content_type,
                        object_id=ui_element.pk,
                        target_field='label',
                        language_code=language_code
                    ).first()

                    if existing:
                        # Update transcript if it differs
                        if existing.transcript != mapping['label_es']:
                            if dry_run:
                                self.stdout.write(
                                    f'Would update transcript for {used_slug}: '
                                    f'"{existing.transcript}" -> "{mapping["label_es"]}"'
                                )
                            else:
                                existing.transcript = mapping['label_es']
                                existing.save()
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'Updated transcript for {used_slug}'
                                    )
                                )
                        else:
                            if dry_run:
                                self.stdout.write(
                                    f'Would skip {mapping["mp3_filename"]} - '
                                    f'AudioSnippet already exists for {used_slug}'
                                )
                            else:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Skipping {mapping["mp3_filename"]} - '
                                        f'AudioSnippet already exists for {used_slug}'
                                    )
                                )
                        skipped_count += 1
                        continue

                    if dry_run:
                        self.stdout.write(
                            f'Would map {mapping["mp3_filename"]} -> {used_slug} ({language_code})'
                        )
                        audio_mapped_count += 1
                        continue

                    # Create AudioSnippet
                    with open(mp3_file, 'rb') as f:
                        audio_file = File(f, name=mapping['mp3_filename'])
                        audio_snippet = AudioSnippet.objects.create(
                            content_type=content_type,
                            object_id=ui_element.pk,
                            target_field='label',
                            language_code=language_code,
                            transcript=mapping['label_es'],
                            status='ready',
                            file=audio_file,
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Mapped {mapping["mp3_filename"]} -> {used_slug} ({language_code})'
                            )
                        )
                        audio_mapped_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'No MP3 file specified for {key} ({used_slug})'
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {key}: {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Created UI elements: {created_count}')
        self.stdout.write(f'  Updated UI elements: {updated_count}')
        self.stdout.write(f'  Mapped audio files: {audio_mapped_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
