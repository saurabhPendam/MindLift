"""
Automatic Model Training Command
Checks if sufficient data is available and trains models automatically
Usage: python manage.py auto_train_models
"""

from django.core.management.base import BaseCommand
from chatbot.adaptive_learning import AdaptiveLearningSystem
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically train ML models if sufficient data is available'

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
            help='Force training even if models already exist'
        )
        parser.add_argument(
            '--min-messages',
            type=int,
            default=50,
            help='Minimum messages required to trigger training (default: 50)'
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress detailed output (for cron jobs)'
        )

    def handle(self, *args, **options):
        days = options['days']
        force = options['force']
        min_messages = options['min_messages']
        quiet = options['quiet']
        
        if not quiet:
            self.stdout.write("=" * 80)
            self.stdout.write(self.style.SUCCESS("🤖 AUTOMATIC MODEL TRAINING"))
            self.stdout.write("=" * 80)
            self.stdout.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Initialize adaptive learning system
        learning_system = AdaptiveLearningSystem()
        
        # Check training data availability
        stats = learning_system.get_training_stats()
        
        if not quiet:
            self.stdout.write("\n📊 TRAINING DATA STATISTICS:")
            self.stdout.write(f"Total messages: {stats['total_messages']}")
            self.stdout.write(f"Analyzed messages: {stats['analyzed_messages']}")
            self.stdout.write(f"Messages with feedback: {stats['messages_with_feedback']}")
            self.stdout.write(f"Users with PHQ-9 assessments: {stats['users_with_phq9']}")
            self.stdout.write(f"Users with GAD-7 assessments: {stats['users_with_gad7']}")
        
        # Check if we have enough data
        if stats['analyzed_messages'] < min_messages and not force:
            message = (
                f"\n⚠️  Insufficient data for training.\n"
                f"Current: {stats['analyzed_messages']} messages\n"
                f"Required: {min_messages} messages\n"
                f"Need {min_messages - stats['analyzed_messages']} more messages.\n"
                f"\nUse --force to train anyway or --min-messages to adjust threshold."
            )
            if not quiet:
                self.stdout.write(self.style.WARNING(message))
            else:
                logger.info(f"Auto-training skipped: Only {stats['analyzed_messages']}/{min_messages} messages")
            return
        
        # Proceed with training
        if not quiet:
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ Sufficient data available - Starting training..."))
            self.stdout.write("=" * 80)
        
        try:
            # Collect training data
            if not quiet:
                self.stdout.write("\n📦 Collecting training data...")
            
            training_data = learning_system.collect_training_data(days=days)
            
            if not quiet:
                self.stdout.write(f"   • Texts: {len(training_data.get('texts', []))}")
                self.stdout.write(f"   • Sentiments: {len(training_data.get('sentiments', []))}")
                self.stdout.write(f"   • Themes: {len(training_data.get('themes', []))}")
                self.stdout.write(f"   • Distortions: {len(training_data.get('distortions', []))}")
            
            training_results = {}
            
            # Train sentiment classifier
            if len(training_data.get('sentiments', [])) >= 30:
                if not quiet:
                    self.stdout.write("\n🧠 Training sentiment classifier...")
                
                result = learning_system.train_sentiment_classifier(
                    training_data['texts'],
                    training_data['sentiments']
                )
                training_results['sentiment'] = result
                
                if not quiet:
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✅ Sentiment Classifier - Accuracy: {result['accuracy']:.2%}"
                    ))
            else:
                if not quiet:
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  Skipping sentiment training (need 30+, have {len(training_data.get('sentiments', []))})"
                    ))
            
            # Train theme classifier
            if len(training_data.get('themes', [])) >= 20:
                if not quiet:
                    self.stdout.write("\n🎯 Training theme classifier...")
                
                result = learning_system.train_theme_classifier(
                    training_data['texts'],
                    training_data['themes']
                )
                training_results['theme'] = result
                
                if not quiet:
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✅ Theme Classifier - Accuracy: {result['accuracy']:.2%}"
                    ))
            else:
                if not quiet:
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  Skipping theme training (need 20+, have {len(training_data.get('themes', []))})"
                    ))
            
            # Train distortion detector
            if len(training_data.get('distortions', [])) >= 15:
                if not quiet:
                    self.stdout.write("\n🧩 Training distortion detector...")
                
                result = learning_system.train_distortion_detector(
                    training_data['texts'],
                    training_data['distortions']
                )
                training_results['distortion'] = result
                
                if not quiet:
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✅ Distortion Detector - Accuracy: {result['accuracy']:.2%}"
                    ))
            else:
                if not quiet:
                    self.stdout.write(self.style.WARNING(
                        f"\n⚠️  Skipping distortion training (need 15+, have {len(training_data.get('distortions', []))})"
                    ))
            
            # Save models
            if training_results:
                if not quiet:
                    self.stdout.write("\n💾 Saving trained models...")
                learning_system.save_models()
                if not quiet:
                    self.stdout.write(self.style.SUCCESS("   ✅ Models saved successfully"))
            
            # Summary
            if not quiet:
                self.stdout.write("\n" + "=" * 80)
                self.stdout.write(self.style.SUCCESS("🎉 TRAINING COMPLETED"))
                self.stdout.write("=" * 80)
                self.stdout.write(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.stdout.write(f"Models trained: {', '.join(training_results.keys())}")
                self.stdout.write("\nNext automatic training will check data again.")
            else:
                logger.info(f"Auto-training completed: {len(training_results)} models trained")
            
        except Exception as e:
            error_msg = f"Error during training: {str(e)}"
            if not quiet:
                self.stdout.write(self.style.ERROR(f"\n❌ {error_msg}"))
            logger.error(error_msg, exc_info=True)
            raise
