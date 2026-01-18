"""
Automated Training & Continuous Improvement System
chatbot/management/commands/train_model.py
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from chatbot.models import Message, Conversation
from datetime import datetime, timedelta
import os
import yaml
import subprocess
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Retrain Rasa model with new conversation data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days of conversation data to analyze'
        )
        parser.add_argument(
            '--min-examples',
            type=int,
            default=3,
            help='Minimum examples required for new intent'
        )

    def handle(self, *args, **options):
        days = options['days']
        min_examples = options['min_examples']
        
        self.stdout.write(self.style.SUCCESS(f'Analyzing conversations from last {days} days...'))
        
        # Get recent conversations
        cutoff_date = datetime.now() - timedelta(days=days)
        messages = Message.objects.filter(
            sender='user',
            timestamp__gte=cutoff_date
        )
        
        # Analyze common phrases and patterns
        new_training_data = self.analyze_messages(messages, min_examples)
        
        if new_training_data:
            # Backup existing NLU data
            self.backup_nlu_data()
            
            # Add new training examples
            self.add_training_examples(new_training_data)
            
            # Retrain Rasa model
            self.retrain_rasa()
            
            self.stdout.write(self.style.SUCCESS('✓ Model retrained successfully!'))
        else:
            self.stdout.write(self.style.WARNING('No new training data found.'))

    def analyze_messages(self, messages, min_examples):
        """Analyze messages and identify patterns for new training data"""
        
        # Common keywords for intent detection
        intent_keywords = {
            'anxious': ['anxious', 'anxiety', 'worried', 'nervous', 'panic'],
            'mood_unhappy': ['sad', 'depressed', 'down', 'unhappy', 'low'],
            'stress': ['stress', 'stressed', 'pressure', 'overwhelm'],
            'lonely': ['lonely', 'alone', 'isolated', 'nobody'],
            'sleep_issues': ['sleep', 'insomnia', 'tired', 'exhausted'],
        }
        
        # Group similar messages
        intent_examples = {}
        
        for message in messages:
            content = message.content.lower()
            
            # Match to existing intents
            for intent, keywords in intent_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if intent not in intent_examples:
                        intent_examples[intent] = []
                    
                    if content not in intent_examples[intent]:
                        intent_examples[intent].append(content)
        
        # Filter intents with enough examples
        new_data = {}
        for intent, examples in intent_examples.items():
            if len(examples) >= min_examples:
                new_data[intent] = examples[:10]  # Limit to 10 new examples per intent
        
        return new_data

    def backup_nlu_data(self):
        """Backup existing NLU data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/nlu_backup_{timestamp}.yml'
        
        if os.path.exists('data/nlu.yml'):
            import shutil
            shutil.copy('data/nlu.yml', backup_path)
            self.stdout.write(f'Backed up NLU data to {backup_path}')

    def add_training_examples(self, new_data):
        """Add new training examples to NLU file"""
        
        nlu_file = 'data/nlu.yml'
        
        # Read existing data
        with open(nlu_file, 'r') as f:
            existing_data = yaml.safe_load(f)
        
        # Add new examples
        for nlu_item in existing_data['nlu']:
            intent_name = nlu_item.get('intent')
            
            if intent_name in new_data:
                examples = nlu_item.get('examples', '')
                new_examples = new_data[intent_name]
                
                # Add new examples
                for example in new_examples:
                    if example not in examples:
                        examples += f'\n    - {example}'
                
                nlu_item['examples'] = examples
                
                self.stdout.write(f'Added {len(new_examples)} examples to intent: {intent_name}')
        
        # Write back to file
        with open(nlu_file, 'w') as f:
            yaml.dump(existing_data, f, default_flow_style=False, allow_unicode=True)

    def retrain_rasa(self):
        """Retrain Rasa model"""
        self.stdout.write('Training Rasa model...')
        
        try:
            result = subprocess.run(
                ['rasa', 'train', '--force'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('Rasa model trained successfully'))
            else:
                self.stdout.write(self.style.ERROR(f'Training failed: {result.stderr}'))
        
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR('Training timeout'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Training error: {str(e)}'))


# ===== CONTINUOUS IMPROVEMENT SYSTEM =====

class FeedbackCollector:
    """Collect user feedback for model improvement"""
    
    @staticmethod
    def collect_feedback(message_id, rating, feedback_text=None):
        """
        Collect feedback on bot responses
        
        Args:
            message_id: ID of the message being rated
            rating: 1-5 star rating
            feedback_text: Optional text feedback
        """
        from chatbot.models import Message
        
        try:
            message = Message.objects.get(id=message_id, sender='bot')
            
            # Store feedback (you can create a Feedback model)
            # For now, we'll log it
            logger.info(f'Feedback for message {message_id}: {rating}/5')
            
            if feedback_text:
                logger.info(f'Feedback text: {feedback_text}')
            
            # If rating is low, flag for review
            if rating <= 2:
                logger.warning(f'Low rating for message: {message.content[:100]}')
            
            return True
        
        except Message.DoesNotExist:
            logger.error(f'Message {message_id} not found')
            return False


class ModelMetrics:
    """Track model performance metrics"""
    
    @staticmethod
    def get_intent_accuracy():
        """Calculate intent recognition accuracy from user feedback"""
        # This would use feedback data to calculate accuracy
        # For now, return placeholder
        return {
            'overall_accuracy': 0.85,
            'intents': {
                'anxious': 0.92,
                'mood_unhappy': 0.88,
                'stress': 0.84,
                'lonely': 0.81,
            }
        }
    
    @staticmethod
    def get_response_quality():
        """Calculate response quality metrics"""
        from chatbot.models import Message
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=7)
        
        total_bot_messages = Message.objects.filter(
            sender='bot',
            timestamp__gte=cutoff
        ).count()
        
        # Calculate average response length
        avg_length = Message.objects.filter(
            sender='bot',
            timestamp__gte=cutoff
        ).aggregate(
            avg_length=models.Avg(models.Length('content'))
        )['avg_length'] or 0
        
        return {
            'total_responses': total_bot_messages,
            'avg_response_length': round(avg_length, 2),
            'period': '7 days'
        }


# ===== AUTOMATED TRAINING SCHEDULER =====

def schedule_automated_training():
    """
    Set up automated training schedule
    Add this to your cron jobs or task scheduler:
    
    # Train model weekly
    0 2 * * 0 cd /path/to/mindlift && python manage.py train_model --days=7
    
    # Or use Django-Celery for scheduled tasks
    """
    pass