"""
Debug Script to Check Sentiment Scores
Save as: chatbot/management/commands/debug_sentiment.py

Run with: python manage.py debug_sentiment
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.models import Message, SentimentReport, Conversation
from chatbot.sentiment_service import SentimentAnalyzer
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Debug sentiment score calculation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to check (optional)',
        )
        parser.add_argument(
            '--session-id',
            type=str,
            help='Session ID to check (optional)',
        )
        parser.add_argument(
            '--reanalyze',
            action='store_true',
            help='Re-analyze all messages',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        session_id = options.get('session_id')
        reanalyze = options.get('reanalyze')
        
        self.stdout.write(self.style.SUCCESS('=== SENTIMENT SCORE DEBUG ===\n'))
        
        # Get user
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found'))
                return
        
        self.stdout.write(f'Checking user: {user.username}\n')
        
        # Get messages
        if session_id:
            try:
                conversation = Conversation.objects.get(session_id=session_id, user=user)
                messages = Message.objects.filter(conversation=conversation, sender='user')
                self.stdout.write(f'Checking conversation: {session_id}\n')
            except Conversation.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Conversation "{session_id}" not found'))
                return
        else:
            messages = Message.objects.filter(
                conversation__user=user,
                sender='user',
                conversation__is_deleted=False
            )
            self.stdout.write(f'Checking all user messages\n')
        
        total_messages = messages.count()
        self.stdout.write(f'Total messages: {total_messages}\n')
        
        if total_messages == 0:
            self.stdout.write(self.style.WARNING('No messages found'))
            return
        
        # Re-analyze if requested
        if reanalyze:
            self.stdout.write(self.style.WARNING('\nRe-analyzing all messages...\n'))
            analyzer = SentimentAnalyzer()
            for i, msg in enumerate(messages, 1):
                result = analyzer.analyze_message(msg)
                self.stdout.write(
                    f'  {i}. Score: {result["score"]:6.3f} | Label: {result["label"]:8s} | Text: {msg.content[:50]}'
                )
            self.stdout.write(self.style.SUCCESS('\n✓ Re-analysis complete\n'))
        
        # Display sentiment scores
        self.stdout.write('\n=== MESSAGE SENTIMENT SCORES ===\n')
        
        messages_with_sentiment = messages.filter(sentiment_score__isnull=False)
        
        if not messages_with_sentiment.exists():
            self.stdout.write(self.style.WARNING('No messages have sentiment scores'))
            return
        
        # Display individual scores
        for i, msg in enumerate(messages_with_sentiment, 1):
            score = msg.sentiment_score or 0.0
            label = msg.sentiment_label or 'unknown'
            self.stdout.write(
                f'{i:3d}. Score: {score:6.3f} | Label: {label:8s} | Text: {msg.content[:60]}'
            )
        
        # Calculate statistics
        self.stdout.write('\n=== STATISTICS ===\n')
        
        scores = [msg.sentiment_score for msg in messages_with_sentiment if msg.sentiment_score is not None]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            positive_count = sum(1 for s in scores if s >= 0.05)
            negative_count = sum(1 for s in scores if s <= -0.05)
            neutral_count = len(scores) - positive_count - negative_count
            
            self.stdout.write(f'Messages analyzed: {len(scores)}')
            self.stdout.write(f'Average score: {avg_score:.3f}')
            self.stdout.write(f'Maximum score: {max_score:.3f}')
            self.stdout.write(f'Minimum score: {min_score:.3f}')
            self.stdout.write(f'\nSentiment Distribution:')
            self.stdout.write(f'  Positive: {positive_count} ({positive_count/len(scores)*100:.1f}%)')
            self.stdout.write(f'  Neutral:  {neutral_count} ({neutral_count/len(scores)*100:.1f}%)')
            self.stdout.write(f'  Negative: {negative_count} ({negative_count/len(scores)*100:.1f}%)')
            
            # Overall sentiment
            if avg_score >= 0.05:
                overall = 'POSITIVE'
                color = self.style.SUCCESS
            elif avg_score <= -0.05:
                overall = 'NEGATIVE'
                color = self.style.ERROR
            else:
                overall = 'NEUTRAL'
                color = self.style.WARNING
            
            self.stdout.write(f'\nOverall Sentiment: {color(overall)}')
        
        # Check recent reports
        self.stdout.write('\n=== RECENT REPORTS ===\n')
        
        recent_reports = SentimentReport.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')[:5]
        
        if recent_reports.exists():
            for report in recent_reports:
                self.stdout.write(
                    f'Report {report.id}: Score={report.average_score:.3f}, '
                    f'Sentiment={report.overall_sentiment}, '
                    f'Messages={report.total_messages}, '
                    f'Created={report.created_at.strftime("%Y-%m-%d %H:%M")}'
                )
        else:
            self.stdout.write('No reports found')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('\n✓ Debug complete\n'))