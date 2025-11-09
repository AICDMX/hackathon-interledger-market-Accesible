from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from jobs.models import Job

User = get_user_model()


class Command(BaseCommand):
    help = 'Load default jobs into the system'

    def handle(self, *args, **options):
        # Get or create a default funder user
        default_funder, created = User.objects.get_or_create(
            username='default_funder',
            defaults={
                'email': 'funder@marketplace.local',
                'role': 'funder',
                'is_staff': True,
            }
        )
        if created:
            default_funder.set_password('default_password_change_me')
            default_funder.save()
            self.stdout.write(
                self.style.SUCCESS(f'Created default funder user: {default_funder.username}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Using existing funder user: {default_funder.username}')
            )

        # Default jobs based on startHere.md
        default_jobs = [
            # Written Languages
            {
                'title': 'Nahuatl Written Translation',
                'description': 'We need written translations in Nahuatl. This job seeks native Nahuatl speakers to provide accurate written translations.',
                'target_language': 'nah',
                'target_dialect': '',
                'deliverable_types': 'text',
                'amount_per_person': Decimal('50.00'),
                'max_responses': 1,
            },
            # Voice in the languages
            {
                'title': 'Otomi Voice Recording',
                'description': 'We need voice recordings in Otomi. Native Otomi speakers are needed to provide high-quality audio recordings.',
                'target_language': 'oto',
                'target_dialect': '',
                'deliverable_types': 'audio',
                'amount_per_person': Decimal('75.00'),
                'max_responses': 1,
            },
            {
                'title': 'Nahuatl Voice Recording',
                'description': 'We need voice recordings in Nahuatl. Native Nahuatl speakers are needed to provide high-quality audio recordings.',
                'target_language': 'nah',
                'target_dialect': '',
                'deliverable_types': 'audio',
                'amount_per_person': Decimal('75.00'),
                'max_responses': 1,
            },
            {
                'title': 'Mazahua Voice Recording',
                'description': 'We need voice recordings in Mazahua. Native Mazahua speakers are needed to provide high-quality audio recordings.',
                'target_language': 'maz',
                'target_dialect': '',
                'deliverable_types': 'audio',
                'amount_per_person': Decimal('75.00'),
                'max_responses': 1,
            },
            {
                'title': 'Quechua Voice Recording',
                'description': 'We need voice recordings in Quechua. Native Quechua speakers are needed to provide high-quality audio recordings.',
                'target_language': 'que',
                'target_dialect': '',
                'deliverable_types': 'audio',
                'amount_per_person': Decimal('75.00'),
                'max_responses': 1,
            },
        ]

        created_count = 0
        skipped_count = 0

        for job_data in default_jobs:
            # Check if job already exists (by title and language)
            existing_job = Job.objects.filter(
                title=job_data['title'],
                target_language=job_data['target_language']
            ).first()

            if existing_job:
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped: Job "{job_data["title"]}" already exists'
                    )
                )
                skipped_count += 1
                continue

            # Calculate budget from amount_per_person * max_responses
            amount_per_person = job_data.get('amount_per_person', Decimal('0.00'))
            max_responses = job_data.get('max_responses', 1)
            budget_total = amount_per_person * max_responses
            
            job = Job.objects.create(
                title=job_data['title'],
                description=job_data['description'],
                target_language=job_data['target_language'],
                target_dialect=job_data['target_dialect'],
                deliverable_types=job_data['deliverable_types'],
                amount_per_person=amount_per_person,
                budget=budget_total,
                max_responses=max_responses,
                funder=default_funder,
                status='recruiting',
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Created job: "{job.title}" ({job.target_language}) - {job.budget} ILP'
                )
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} jobs, skipped {skipped_count} existing jobs'
            )
        )
