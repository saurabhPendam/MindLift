"""
Management command to add authorized emails
Usage: python manage.py add_authorized_email email@gmail.com
"""

from django.core.management.base import BaseCommand
from chatbot.models import AuthorizedEmail


class Command(BaseCommand):
    help = 'Add an authorized Gmail account'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Gmail address to authorize')
        parser.add_argument(
            '--notes',
            type=str,
            default='',
            help='Optional notes about this email'
        )

    def handle(self, *args, **options):
        email = options['email'].lower().strip()
        notes = options['notes']

        # Validate Gmail
        if not email.endswith('@gmail.com'):
            self.stdout.write(self.style.ERROR(
                f'Error: {email} is not a Gmail address'
            ))
            return

        # Check if already exists
        if AuthorizedEmail.objects.filter(email=email).exists():
            existing = AuthorizedEmail.objects.get(email=email)
            if existing.is_active:
                self.stdout.write(self.style.WARNING(
                    f'Email {email} is already authorized'
                ))
            else:
                # Reactivate
                existing.is_active = True
                existing.notes = notes if notes else existing.notes
                existing.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Reactivated email: {email}'
                ))
            return

        # Create new authorized email
        AuthorizedEmail.objects.create(
            email=email,
            is_active=True,
            notes=notes
        )

        self.stdout.write(self.style.SUCCESS(
            f'✓ Successfully authorized email: {email}'
        ))
