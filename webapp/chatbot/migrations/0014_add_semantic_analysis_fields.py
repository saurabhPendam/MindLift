# Generated migration for semantic analysis fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0013_feedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='themes',
            field=models.JSONField(default=dict, blank=True, help_text='Mental health themes detected (anxiety, depression, etc.)'),
        ),
        migrations.AddField(
            model_name='message',
            name='cognitive_distortions',
            field=models.JSONField(default=dict, blank=True, help_text='CBT cognitive distortions detected'),
        ),
        migrations.AddField(
            model_name='message',
            name='coping_indicators',
            field=models.JSONField(default=list, blank=True, help_text='Positive coping strategies mentioned'),
        ),
        migrations.AddField(
            model_name='message',
            name='crisis_level',
            field=models.CharField(max_length=20, null=True, blank=True, help_text='Crisis urgency: immediate, high, moderate, none'),
        ),
        migrations.AddField(
            model_name='message',
            name='crisis_confidence',
            field=models.FloatField(null=True, blank=True, help_text='Confidence score for crisis detection'),
        ),
        migrations.AddField(
            model_name='message',
            name='key_phrases',
            field=models.JSONField(default=list, blank=True, help_text='Important phrases extracted from message'),
        ),
        migrations.AddField(
            model_name='message',
            name='linguistic_features',
            field=models.JSONField(default=dict, blank=True, help_text='Linguistic analysis (word count, first-person ratio, etc.)'),
        ),
        migrations.AddField(
            model_name='message',
            name='semantic_similarity',
            field=models.FloatField(null=True, blank=True, help_text='Average semantic similarity with conversation history'),
        ),
        # Add indexes for common queries
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['crisis_level'], name='msg_crisis_lvl_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['sender', 'timestamp'], name='msg_sender_time_idx'),
        ),
    ]
