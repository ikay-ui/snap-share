# management/commands/createsuperuser_if_none_exists.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if User.objects.filter(is_admin=True).count() == 0:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
            first_name = os.environ.get('DJANGO_SUPERUSER_FIRSTNAME', 'Admin')
            last_name = os.environ.get('DJANGO_SUPERUSER_LASTNAME', 'User')
            
            print('Creating superuser account...')
            
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Ensure the user is active and has all required permissions
            user.is_active = True
            user.is_admin = True
            user.is_staff = True
            user.save()
            
            print('Superuser account created successfully')
        else:
            print('Superuser account already exists')