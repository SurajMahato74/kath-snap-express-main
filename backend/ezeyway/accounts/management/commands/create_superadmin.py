from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superadmin user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username for the superadmin')
        parser.add_argument('--email', type=str, help='Email for the superadmin')
        parser.add_argument('--password', type=str, help='Password for the superadmin')

    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                user_type='superuser',
                is_staff=True,
                is_superuser=True,
                is_verified=True,
                email_verified=True,
                plain_password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superadmin user: {username}')
            )
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(f'User with username "{username}" already exists')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superadmin: {str(e)}')
            )