"""
Django management command to train adaptive learning models
Usage: python manage.py train_adaptive_models [--days DAYS] [--force]
"""

from django.core.management.base import BaseCommand
from chatbot.adaptive_learning import adaptive_learning
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train adaptive learning models from user interaction data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of data to use for training (default: 90)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retraining even if models exist'
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Show training data statistics only, do not train'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        force = options['force']
        stats_only = options['stats_only']
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('MindLift Adaptive Learning System'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # Show statistics
        self.stdout.write(self.style.HTTP_INFO('\n📊 Training Data Statistics:'))
        stats = adaptive_learning.get_training_stats()
        
        self.stdout.write(f"\n  Total user messages: {stats['total_messages']}")
        self.stdout.write(f"  Messages with sentiment: {stats['analyzed_messages']}")
        self.stdout.write(f"  Messages with user feedback: {stats['messages_with_feedback']}")
        self.stdout.write(f"  Users with PHQ-9 assessments: {stats['users_with_phq9']}")
        self.stdout.write(f"  Users with GAD-7 assessments: {stats['users_with_gad7']}")
        
        if stats.get('sentiment_model'):
            self.stdout.write(f"\n  📈 Current Sentiment Model:")
            self.stdout.write(f"    Accuracy: {stats['sentiment_model']['accuracy']:.2%}")
            self.stdout.write(f"    Trained: {stats['sentiment_model']['trained_date']}")
        
        if stats_only:
            self.stdout.write(self.style.SUCCESS('\n✅ Statistics displayed successfully'))
            return
        
        # Check if models exist
        if not force:
            if adaptive_learning.sentiment_model:
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  Models already exist. Use --force to retrain.'
                ))
                response = input('Continue with retraining? (y/N): ')
                if response.lower() != 'y':
                    self.stdout.write('Training cancelled.')
                    return
        
        # Train models
        self.stdout.write(self.style.HTTP_INFO(f'\n🔄 Starting model training with {days} days of data...'))
        
        try:
            results = adaptive_learning.retrain_all_models(days=days)
            
            self.stdout.write(self.style.HTTP_INFO('\n📝 Training Results:'))
            
            if results.get('sentiment'):
                self.stdout.write(self.style.SUCCESS('  ✅ Sentiment Classifier: Trained'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  Sentiment Classifier: Insufficient data'))
            
            if results.get('theme'):
                self.stdout.write(self.style.SUCCESS('  ✅ Theme Extractor: Trained'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  Theme Extractor: Insufficient data'))
            
            if results.get('distortion'):
                self.stdout.write(self.style.SUCCESS('  ✅ Distortion Detector: Trained'))
            else:
                self.stdout.write(self.style.WARNING('  ⚠️  Distortion Detector: Insufficient data'))
            
            # Show updated stats
            self.stdout.write(self.style.HTTP_INFO('\n📊 Updated Model Statistics:'))
            updated_stats = adaptive_learning.get_training_stats()
            
            if updated_stats.get('sentiment_model'):
                self.stdout.write(f"  Sentiment Model Accuracy: {updated_stats['sentiment_model']['accuracy']:.2%}")
            
            self.stdout.write(self.style.SUCCESS('\n✅ Training complete! Models saved to ml_models/'))
            self.stdout.write('\nUsage Tips:')
            self.stdout.write('  • Run this weekly/monthly to improve accuracy')
            self.stdout.write('  • More user feedback = better models')
            self.stdout.write('  • Clinical assessments help validate predictions')
            self.stdout.write('  • Use --stats-only to check data without training')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Training failed: {str(e)}'))
            logger.error(f'Training error: {e}', exc_info=True)
            
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
