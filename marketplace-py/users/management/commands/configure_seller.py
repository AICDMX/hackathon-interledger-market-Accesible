"""
Management command to configure seller credentials for a user account.
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure seller credentials for a user account (marketplace account)'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user to configure as seller'
        )
        parser.add_argument(
            '--wallet-address',
            type=str,
            required=True,
            help='Open Payments wallet address URL (e.g., https://ilp.interledger-test.dev/seller)'
        )
        parser.add_argument(
            '--key-id',
            type=str,
            required=True,
            help='Key identifier for seller wallet'
        )
        parser.add_argument(
            '--private-key',
            type=str,
            help='Private key in PEM format (or path to file containing private key)'
        )
        parser.add_argument(
            '--private-key-file',
            type=str,
            help='Path to file containing private key in PEM format'
        )

    def handle(self, *args, **options):
        username = options['username']
        wallet_address = options['wallet_address']
        key_id = options['key_id']
        
        # Get private key from file or direct input
        private_key = options.get('private_key')
        private_key_file = options.get('private_key_file')
        
        if private_key_file:
            try:
                with open(private_key_file, 'r') as f:
                    private_key = f.read()
            except FileNotFoundError:
                raise CommandError(f'Private key file not found: {private_key_file}')
            except Exception as e:
                raise CommandError(f'Error reading private key file: {e}')
        
        if not private_key:
            raise CommandError('Either --private-key or --private-key-file must be provided')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User not found: {username}')
        
        # Update seller credentials
        user.seller_wallet_address = wallet_address
        user.seller_key_id = key_id
        user.seller_private_key = private_key
        user.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully configured seller credentials for user: {username}\n'
                f'  Wallet Address: {wallet_address}\n'
                f'  Key ID: {key_id}'
            )
        )
