"""
Management command to test semantic analyzer
Usage: python manage.py test_semantic_analyzer
"""

from django.core.management.base import BaseCommand
from chatbot.semantic_analyzer import semantic_analyzer
import json


class Command(BaseCommand):
    help = 'Test semantic analyzer with sample texts'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Semantic Analyzer'))
        self.stdout.write('=' * 80)
        
        # Test cases
        test_cases = [
            {
                'text': "I'm feeling really anxious about my job interview tomorrow. I always mess up these things.",
                'history': [
                    "I've been stressed about work lately",
                    "I can't seem to sleep well at night"
                ]
            },
            {
                'text': "Nobody likes me. Everyone thinks I'm a failure. I should just give up.",
                'history': [
                    "Had a bad day today",
                    "My boss criticized my work again"
                ]
            },
            {
                'text': "I've been trying meditation and breathing exercises. They help a bit.",
                'history': [
                    "Feeling overwhelmed",
                    "Started seeing a therapist"
                ]
            },
            {
                'text': "I can't take this anymore. I just want to end it all.",
                'history': []
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO(f'Test Case {i}:'))
            self.stdout.write(f'Text: {case["text"]}')
            
            # Run analysis
            result = semantic_analyzer.analyze_text(
                text=case['text'],
                conversation_history=case['history']
            )
            
            # Generate insights
            insights = semantic_analyzer.generate_insights(result)
            
            # Display results
            self.stdout.write(self.style.WARNING('\nThemes:'))
            for theme, score in list(result['themes'].items())[:3]:
                self.stdout.write(f'  • {theme}: {score:.3f}')
            
            if result['cognitive_distortions']:
                self.stdout.write(self.style.WARNING('\nCognitive Distortions:'))
                for distortion, patterns in result['cognitive_distortions'].items():
                    self.stdout.write(f'  • {distortion}: {patterns}')
            
            if result['coping_indicators']:
                self.stdout.write(self.style.SUCCESS('\nCoping Strategies:'))
                for strategy in result['coping_indicators']:
                    self.stdout.write(f'  • {strategy}')
            
            crisis = result['crisis_level']
            if crisis['level'] != 'none':
                self.stdout.write(self.style.ERROR(f'\nCrisis Level: {crisis["level"].upper()}'))
                self.stdout.write(f'  Confidence: {crisis["confidence"]:.2f}')
                self.stdout.write(f'  Patterns: {crisis["matched_patterns"]}')
            
            if result['key_phrases']:
                self.stdout.write(self.style.WARNING('\nKey Phrases:'))
                self.stdout.write(f'  {", ".join(result["key_phrases"])}')
            
            if insights:
                self.stdout.write(self.style.SUCCESS('\nInsights:'))
                for key, value in insights.items():
                    self.stdout.write(f'  • {key}: {value}')
            
            ling = result['linguistic_features']
            self.stdout.write(self.style.HTTP_INFO('\nLinguistic Features:'))
            self.stdout.write(f'  Words: {ling["word_count"]}, Sentences: {ling["sentence_count"]}')
            self.stdout.write(f'  First-person ratio: {ling["first_person_ratio"]:.2%}')
            self.stdout.write(f'  Negative word ratio: {ling["negative_word_ratio"]:.2%}')
            
            if result['semantic_similarity']:
                sim = result['semantic_similarity']
                self.stdout.write(self.style.HTTP_INFO('\nSemantic Similarity:'))
                self.stdout.write(f'  Avg: {sim["avg_similarity"]:.3f}, Max: {sim["max_similarity"]:.3f}')
            
            self.stdout.write('-' * 80)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Semantic Analyzer Test Complete'))
