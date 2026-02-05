"""
Test script to verify recommendations display without ** formatting
"""
from chatbot.sentiment_service import ReportGenerator

# Create test data
generator = ReportGenerator()

# Generate recommendations with themes and distortions
semantic_insights = {
    'themes': {
        'anxiety': 0.15,
        'work_stress': 0.12
    },
    'cognitive_distortions': {
        'catastrophizing': ['worst', 'terrible'],
        'all_or_nothing': ['always', 'never']
    },
    'coping_strategies': {
        'breathing': 3,
        'meditation': 2
    },
    'crisis_summary': {
        'immediate': 0,
        'high': 0,
        'moderate': 0
    }
}

# Generate recommendations
recs = generator._generate_recommendations(
    sentiment='negative',
    score=-0.35,
    emotions={'anxiety': 4, 'fear': 3},
    trend='declining',
    semantic_insights=semantic_insights
)

print('Sample Recommendation Output:')
print('=' * 80)
# Show first 15 lines
lines = recs.split('\n')
for i, line in enumerate(lines[:15], 1):
    print(f'{i}. {line}')
print(f'\n... and {len(lines) - 15} more lines\n')
print('=' * 80)
print(f'Total lines: {len(lines)}')
print(f'Total characters: {len(recs)}')
has_asterisks = '**' in recs
print(f'Contains **: {has_asterisks}')
if not has_asterisks:
    print('✅ All markdown formatting removed!')
else:
    print('❌ Still has ** formatting')
