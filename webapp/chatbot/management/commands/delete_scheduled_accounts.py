"""
Management command to delete accounts that have passed their grace period
Save as: chatbot/management/commands/delete_scheduled_accounts.py

Run with: python manage.py delete_scheduled_accounts

Add to crontab for daily execution:
0 2 * * * cd /path/to/project && python manage.py delete_scheduled_accounts
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from chatbot.models import UserProfile, AuditLog
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete user accounts that have passed their grace period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.SUCCESS('Starting account deletion check...'))
        
        # Find profiles with deletion scheduled for today or earlier
        now = timezone.now()
        profiles_to_delete = UserProfile.objects.filter(
            deletion_requested=True,
            deletion_scheduled_for__lte=now
        ).select_related('user')
        
        deletion_count = profiles_to_delete.count()
        
        if deletion_count == 0:
            self.stdout.write(self.style.SUCCESS('No accounts scheduled for deletion'))
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {deletion_count} account(s) scheduled for deletion')
        )
        
        for profile in profiles_to_delete:
            user = profile.user
            username = user.username
            user_id = user.id
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] Would delete: {username} (ID: {user_id}, '
                        f'Scheduled: {profile.deletion_scheduled_for})'
                    )
                )
            else:
                try:
                    # Log deletion before deleting user
                    AuditLog.objects.create(
                        user=user,
                        action='scheduled_account_deletion',
                        description=f'Account {username} automatically deleted after grace period',
                        category='deletion'
                    )
                    
                    # Delete user (cascades to all related data)
                    user.delete()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Deleted account: {username} (ID: {user_id})'
                        )
                    )
                    
                    logger.info(f'Scheduled deletion completed for user: {username} (ID: {user_id})')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error deleting {username}: {str(e)}')
                    )
                    logger.error(f'Error in scheduled deletion for {username}: {str(e)}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n[DRY RUN] No accounts were actually deleted. '
                    'Run without --dry-run to perform deletions.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Completed: {deletion_count} account(s) deleted'
                )
            )