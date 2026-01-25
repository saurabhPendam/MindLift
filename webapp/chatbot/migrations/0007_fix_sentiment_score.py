"""
Migration to ensure sentiment_score field is properly configured
Save as: chatbot/migrations/0007_fix_sentiment_score.py

Run with: python manage.py migrate
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0006_remove_auditlog_audit_timestamp_idx_and_more'),
    ]

    operations = [
        # Ensure sentiment_score in Message is FloatField with proper precision
        migrations.AlterField(
            model_name='message',
            name='sentiment_score',
            field=models.FloatField(null=True, blank=True, db_index=True),
        ),
        
        # Ensure average_score in SentimentReport is FloatField with proper precision
        migrations.AlterField(
            model_name='sentimentreport',
            name='average_score',
            field=models.FloatField(db_index=True),
        ),
        
        # Add helpful indexes for performance
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sentiment_label', 'timestamp'], name='msg_sent_label_time_idx'),
        ),
        
        migrations.AddIndex(
            model_name='sentimentreport',
            index=models.Index(fields=['user', '-created_at'], name='report_user_time_idx'),
        ),
    ]