# chatbot/migrations/0004_add_performance_indexes.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0002_message_contains_crisis_keywords_and_more'),
    ]

    operations = [
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
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['contains_crisis_keywords'], name='msg_crisis_idx'),
        ),
    ]