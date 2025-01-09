# management/commands/createsuperuser_if_none_exists.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates a superuser if none exists'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).count() == 0:
            username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
            email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')
            
            print('Creating superuser account...')
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print('Superuser account created successfully')
        else:
            print('Superuser account already exists')