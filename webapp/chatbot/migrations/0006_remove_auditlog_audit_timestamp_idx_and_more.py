# chatbot/migrations/0006_remove_auditlog_audit_timestamp_idx_and_more.py

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0005_merge_20260121_1027'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='auditlog',
            name='audit_timestamp_idx',
        ),
        migrations.RemoveIndex(
            model_name='auditlog',
            name='audit_category_idx',
        ),
        migrations.RemoveIndex(
            model_name='message',
            name='msg_crisis_idx',
        ),
        migrations.RemoveIndex(
            model_name='sentimentreport',
            name='report_deleted_idx',
        ),
    ]
