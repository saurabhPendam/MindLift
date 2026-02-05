"""
Test personalized recommendations output
"""

from django.core.management.base import BaseCommand
from chatbot.sentiment_service import ReportGenerator


class Command(BaseCommand):
    help = 'Test personalized recommendations output'
    
    def handle(self, *args, **options):
        # Simulate user with rich semantic data
        semantic_insights = {
            'themes': {
                'anxiety': 0.15,
                'work_stress': 0.12,
                'sleep': 0.08
            },
            'cognitive_distortions': {
                'catastrophizing': ['worst', 'terrible', 'disaster'],
                'all_or_nothing': ['always', 'never'],
                'should_statements': ['should', 'must']
            },
            'coping_strategies': {
                'breathing': 3,
                'meditation': 2,
                'exercise': 1
            },
            'crisis_levels': {
                'immediate': 0,
                'high': 0,
                'moderate': 1
            },
            'linguistic_patterns': {
                'avg_first_person_ratio': 0.22,
                'avg_negative_word_ratio': 0.13
            }
        }

        emotions = {
            'anxiety': 4,
            'fear': 3,
            'sadness': 2
        }

        generator = ReportGenerator()

        # Generate recommendations
        recommendations = generator._generate_recommendations(
            sentiment='negative',
            score=-0.45,
            emotions=emotions,
            trend='declining',
            semantic_insights=semantic_insights
        )

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("FULL PERSONALIZED RECOMMENDATIONS OUTPUT"))
        self.stdout.write("=" * 80)
        self.stdout.write(recommendations)
        self.stdout.write("=" * 80)
        self.stdout.write(f"\nTotal lines: {len(recommendations.split(chr(10)))}")
        self.stdout.write(f"Total characters: {len(recommendations)}")
        
        # Show what frontend will display
        self.stdout.write("\n\n" + "=" * 80)
        self.stdout.write(self.style.WARNING("FRONTEND DISPLAY (split by \\n):"))
        self.stdout.write("=" * 80)
        rec_lines = recommendations.split('\n')
        for i, line in enumerate(rec_lines[:20], 1):  # Show first 20 lines
            if line.strip():
                self.stdout.write(f"{i}. {line}")
        
        if len(rec_lines) > 20:
            self.stdout.write(f"\n... and {len(rec_lines) - 20} more lines")
