import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Load demo users into the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default=None,
            help='Path to JSON file containing demo users (default: data/demo_users.json)',
        )

    def handle(self, *args, **options):
        # Determine JSON file path
        json_file = options.get('json_file')
        if json_file is None:
            # Default to data/demo_users.json at project root
            # Get project root (parent of marketplace-py)
            current_file = os.path.abspath(__file__)
            # Go up: commands -> management -> users -> marketplace-py -> project root
            # __file__ is at: marketplace-py/users/management/commands/load_demo_users.py
            # Need 5 dirname calls to get to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file)))))
            json_file = os.path.join(project_root, 'data', 'demo_users.json')

        # Load users from JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                demo_users = json.load(f)
            self.stdout.write(
                self.style.SUCCESS(f'Loaded {len(demo_users)} users from {json_file}')
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

        for user_data in demo_users:
            try:
                # Check if user already exists (by username)
                username = user_data['username']
                existing_user = User.objects.filter(username=username).first()

                if existing_user:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Skipped: User "{username}" already exists'
                        )
                    )
                    skipped_count += 1
                    continue

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=user_data.get('email', ''),
                    password=user_data.get('password', 'demo123'),
                    first_name=user_data.get('first_name', ''),
                    last_name=user_data.get('last_name', ''),
                    pretty_name=user_data.get('pretty_name', ''),
                    role=user_data.get('role', 'both'),
                    preferred_language=user_data.get('preferred_language', 'en'),
                    native_languages=user_data.get('native_languages', ''),
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created user: "{user.username}" ({user.get_role_display()}) - {user.email}'
                    )
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating user "{user_data.get("username", "Unknown")}": {e}'
                    )
                )
                error_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: Created {created_count} users, skipped {skipped_count} existing users'
            )
        )
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Errors encountered: {error_count} users failed to create')
            )
