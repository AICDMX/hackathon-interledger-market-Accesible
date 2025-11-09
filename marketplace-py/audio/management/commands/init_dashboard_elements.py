"""
Management command to initialize StaticUIElement objects for dashboard items.
"""
from django.core.management.base import BaseCommand
from audio.models import StaticUIElement
from jobs.audio_support import AUDIO_SUPPORT_OPPORTUNITIES


class Command(BaseCommand):
    help = 'Initialize StaticUIElement objects for dashboard items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        created_count = 0
        updated_count = 0
        
        # Map of slugs to their display labels
        slug_to_label = {
            'job_post': 'Publicar trabajo',
            'my_products': 'Mis productos',
            'my_money': 'Mi dinero',
            'pending_jobs': 'Mis trabajos por terminar',
            'page_1': 'P?gina 1',
            'page_2': 'P?gina 2',
        }
        
        slug_to_label_en = {
            'job_post': 'Job Post',
            'my_products': 'My Products',
            'my_money': 'My Money',
            'pending_jobs': 'My Pending to Finish Jobs',
            'page_1': 'Page 1',
            'page_2': 'Page 2',
        }
        
        for slug, opportunity in AUDIO_SUPPORT_OPPORTUNITIES.items():
            if slug not in slug_to_label:
                self.stdout.write(self.style.WARNING(f'Skipping {slug} - no label mapping'))
                continue
                
            label_es = slug_to_label[slug]
            label_en = slug_to_label_en.get(slug, opportunity.target_field)
            
            # Try different slug formats that the API might use
            slug_candidates = [
                slug,  # e.g., "job_post"
                f'dashboard_{slug}',  # e.g., "dashboard_job_post"
            ]
            
            for candidate_slug in slug_candidates:
                if dry_run:
                    try:
                        existing = StaticUIElement.objects.get(slug=candidate_slug)
                        self.stdout.write(
                            self.style.WARNING(f'Would update: {candidate_slug} ({existing.label_es})')
                        )
                    except StaticUIElement.DoesNotExist:
                        self.stdout.write(
                            self.style.SUCCESS(f'Would create: {candidate_slug} ({label_es})')
                        )
                else:
                    ui_element, created = StaticUIElement.objects.get_or_create(
                        slug=candidate_slug,
                        defaults={
                            'label_es': label_es,
                            'label_en': label_en,
                            'category': 'dashboard',
                            'description': opportunity.description_es,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Created: {candidate_slug} ({label_es})')
                        )
                    else:
                        # Update existing
                        ui_element.label_es = label_es
                        ui_element.label_en = label_en
                        ui_element.category = 'dashboard'
                        if not ui_element.description:
                            ui_element.description = opportunity.description_es
                        ui_element.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Updated: {candidate_slug} ({label_es})')
                        )
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\nDry run complete. Use without --dry-run to create/update.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nComplete! Created {created_count} elements, updated {updated_count} elements.'
                )
            )
