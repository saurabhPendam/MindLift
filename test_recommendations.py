"""
Test script to see full personalized recommendations output
Run: python manage.py shell < test_recommendations.py
"""

from chatbot.sentiment_service import ReportGenerator

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

print("=" * 80)
print("FULL PERSONALIZED RECOMMENDATIONS OUTPUT")
print("=" * 80)
print(recommendations)
print("=" * 80)
print(f"\nTotal lines: {len(recommendations.split(chr(10)))}")
print(f"Total characters: {len(recommendations)}")
