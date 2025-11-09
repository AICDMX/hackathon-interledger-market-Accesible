import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from jobs.models import Job

User = get_user_model()


class Command(BaseCommand):
    help = 'Load default jobs into the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default=None,
            help='Path to JSON file containing default jobs (default: jobs/fixtures/default_jobs.json)',
        )

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

        # Determine JSON file path
        json_file = options.get('json_file')
        if json_file is None:
            # Default to data/default_jobs.json at project root
            # Get project root (parent of marketplace-py)
            current_file = os.path.abspath(__file__)
            # Go up: commands -> management -> jobs -> marketplace-py -> project root
            # __file__ is at: marketplace-py/jobs/management/commands/load_default_jobs.py
            # Need 5 dirname calls to get to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
            json_file = os.path.join(project_root, 'data', 'default_jobs.json')

        # Load jobs from JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                default_jobs = json.load(f)
            self.stdout.write(
                self.style.SUCCESS(f'Loaded {len(default_jobs)} jobs from {json_file}')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'JSON file not found: {json_file}')
            )
            return
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON in {json_file}: {e}')
            )
            return

        created_count = 0
        skipped_count = 0
        error_count = 0

        for job_data in default_jobs:
            try:
                # Check if job already exists (by title and language)
                target_language_code = job_data.get('target_language_code', '')
                existing_job = Job.objects.filter(
                    title=job_data['title'],
                    target_language=target_language_code
                ).first()

                if existing_job:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped: Job "{job_data["title"]}" already exists'
                        )
                    )
                    skipped_count += 1
                    continue

                # Extract job fields from JSON
                amount_per_person = Decimal(str(job_data.get('amount_per_person', job_data.get('budget_mxn', 0))))
                max_responses = job_data.get('max_responses', 1)
                budget_total = amount_per_person * max_responses
                
                # Get status from JSON, default to 'recruiting' if not specified
                job_status = job_data.get('status', 'recruiting')
                
                job = Job.objects.create(
                    title=job_data['title'],
                    description=job_data['description'],
                    target_language=target_language_code,
                    target_dialect=job_data.get('target_dialect', ''),
                    deliverable_types=job_data.get('deliverable_types', 'text'),
                    amount_per_person=amount_per_person,
                    budget=budget_total,
                    max_responses=max_responses,
                    funder=default_funder,
                    status=job_status,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created job: "{job.title}" ({job.target_language}) - {job.budget} ILP'
                    )
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating job "{job_data.get("title", "Unknown")}": {e}'
                    )
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} jobs, skipped {skipped_count} existing jobs'
            )
        )
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Errors encountered: {error_count} jobs failed to create')
            )
