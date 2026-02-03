# Generated migration for 2FA and authorized emails

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chatbot', '0009_remove_mood_score_field'),
    ]

    operations = [
        # Add 2FA fields to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='two_factor_enabled',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='two_factor_secret',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_authorized_email',
            field=models.BooleanField(default=False),
        ),
        
        # Create OTPVerification model
        migrations.CreateModel(
            name='OTPVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('attempt_count', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='otp_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'otp_verifications',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create AuthorizedEmail model
        migrations.CreateModel(
            name='AuthorizedEmail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='added_authorized_emails', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'authorized_emails',
                'ordering': ['-added_at'],
            },
        ),
        
        # Update AuditLog Meta class
        migrations.AlterModelOptions(
            name='auditlog',
            options={'ordering': ['-timestamp']},
        ),
    ]
