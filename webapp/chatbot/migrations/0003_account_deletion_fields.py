# Generated migration for account deletion and AI safety features
# File: chatbot/migrations/0003_account_deletion_fields.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chatbot', '0001_initial'),
    ]

    operations = [
        # UserProfile - Account Deletion Fields
        migrations.AddField(
            model_name='userprofile',
            name='deletion_requested',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deletion_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deletion_scheduled_for',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # SentimentReport - Soft Delete Fields
        migrations.AddField(
            model_name='sentimentreport',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sentimentreport',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Message - AI Safety Fields
        migrations.AddField(
            model_name='message',
            name='contains_crisis_keywords',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='requires_professional_referral',
            field=models.BooleanField(default=False),
        ),
        
        # Create AuditLog Model
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('category', models.CharField(
                    choices=[
                        ('account', 'Account Management'),
                        ('data', 'Data Access'),
                        ('security', 'Security Event'),
                        ('crisis', 'Crisis Detection'),
                        ('deletion', 'Data Deletion')
                    ],
                    default='account',
                    max_length=50
                )),
                ('user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'db_table': 'audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes for performance
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['-timestamp'], name='audit_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['category'], name='audit_category_idx'),
        ),
        migrations.AddIndex(
            model_name='sentimentreport',
            index=models.Index(fields=['is_deleted'], name='report_deleted_idx'),
        ),
    ]