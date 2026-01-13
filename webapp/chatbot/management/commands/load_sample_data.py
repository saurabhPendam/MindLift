"""
Management command to load sample data
Save this as: chatbot/management/commands/load_sample_data.py

Directory structure:
chatbot/
    management/
        __init__.py
        commands/
            __init__.py
            load_sample_data.py
"""

from django.core.management.base import BaseCommand
from chatbot.models import Activity, MotivationalQuote


class Command(BaseCommand):
    help = 'Load sample activities and quotes into database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to load sample data...'))
        
        # Create sample activities
        activities_data = [
            {
                'title': '5-Minute Breathing Exercise',
                'description': 'Deep breathing to reduce anxiety and stress',
                'category': 'breathing',
                'duration_minutes': 5,
                'difficulty': 'easy',
                'instructions': '1. Sit comfortably with your back straight\n2. Close your eyes\n3. Breathe in slowly through your nose for 4 counts\n4. Hold your breath for 4 counts\n5. Breathe out slowly through your mouth for 4 counts\n6. Repeat 10 times',
                'video_url': 'https://www.youtube.com/embed/tybOi4hjZFQ',
                'is_active': True
            },
            {
                'title': '10-Minute Guided Meditation',
                'description': 'Calm your mind with guided meditation',
                'category': 'meditation',
                'duration_minutes': 10,
                'difficulty': 'easy',
                'instructions': '1. Find a quiet space\n2. Sit comfortably\n3. Close your eyes\n4. Follow the guided meditation\n5. Focus on your breath',
                'video_url': 'https://www.youtube.com/embed/ZToicYcHIOU',
                'is_active': True
            },
            {
                'title': 'Progressive Muscle Relaxation',
                'description': 'Release physical tension through systematic muscle relaxation',
                'category': 'relaxation',
                'duration_minutes': 15,
                'difficulty': 'easy',
                'instructions': '1. Find a comfortable position\n2. Tense each muscle group for 5 seconds\n3. Release and relax for 10 seconds\n4. Move through all major muscle groups\n5. Focus on the sensation of relaxation',
                'video_url': 'https://www.youtube.com/embed/ClqPtWzozXs',
                'is_active': True
            },
            {
                'title': 'Mood-Boosting Walk',
                'description': 'A 15-minute outdoor walk to lift your spirits',
                'category': 'physical',
                'duration_minutes': 15,
                'difficulty': 'easy',
                'instructions': '1. Put on comfortable shoes\n2. Step outside\n3. Walk at a comfortable pace\n4. Focus on your surroundings\n5. Take deep breaths',
                'video_url': 'https://www.youtube.com/embed/CZTAjfJ8umA',
                'is_active': True
            },
            {
                'title': 'Gratitude Journaling',
                'description': 'Write down three things you\'re grateful for',
                'category': 'creative',
                'duration_minutes': 10,
                'difficulty': 'easy',
                'instructions': '1. Find a quiet space\n2. Take out a journal or open a notes app\n3. Write down three things you\'re grateful for today\n4. Reflect on why these things matter to you\n5. Notice how you feel after this exercise',
                'is_active': True
            },
            {
                'title': 'Morning Gratitude Practice',
                'description': 'Start your day with gratitude',
                'category': 'mindfulness',
                'duration_minutes': 10,
                'difficulty': 'easy',
                'instructions': '1. Find a quiet space\n2. Take 3 deep breaths\n3. Think of 3 things you\'re grateful for\n4. Write them down or say them out loud',
                'is_active': True
            },
            {
                'title': 'Quick Stretching Routine',
                'description': 'Release tension with gentle stretches',
                'category': 'physical',
                'duration_minutes': 10,
                'difficulty': 'easy',
                'instructions': '1. Stand with feet shoulder-width apart\n2. Stretch arms overhead\n3. Bend to each side\n4. Roll shoulders\n5. Neck stretches',
                'video_url': 'https://www.youtube.com/embed/g_tea8ZNk5A',
                'is_active': True
            },
            {
                'title': 'Mindful Coloring',
                'description': 'Relax through creative expression',
                'category': 'creative',
                'duration_minutes': 20,
                'difficulty': 'easy',
                'instructions': '1. Get coloring materials (digital or physical)\n2. Choose a design\n3. Focus on the colors and patterns\n4. Let your mind relax\n5. Don\'t worry about perfection',
                'is_active': True
            },
            {
                'title': 'Social Connection Call',
                'description': 'Reach out to a friend or family member',
                'category': 'social',
                'duration_minutes': 15,
                'difficulty': 'medium',
                'instructions': '1. Think of someone you care about\n2. Call or video chat with them\n3. Share how you\'re feeling\n4. Listen to their experiences\n5. Express gratitude for the connection',
                'is_active': True
            },
        ]
        
        activity_count = 0
        for activity_data in activities_data:
            activity, created = Activity.objects.get_or_create(
                title=activity_data['title'],
                defaults=activity_data
            )
            if created:
                activity_count += 1
                self.stdout.write(f"  Created activity: {activity.title}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {activity_count} activities'))
        
        # Create sample motivational quotes
        quotes_data = [
            {
                'quote': 'You are braver than you believe, stronger than you seem, and smarter than you think.',
                'author': 'A.A. Milne',
                'category': 'motivation',
                'is_active': True
            },
            {
                'quote': 'Mental health is not a destination, but a process. It\'s about how you drive, not where you\'re going.',
                'author': 'Noam Shpancer',
                'category': 'inspiration',
                'is_active': True
            },
            {
                'quote': 'You don\'t have to control your thoughts. You just have to stop letting them control you.',
                'author': 'Dan Millman',
                'category': 'strength',
                'is_active': True
            },
            {
                'quote': 'Healing takes time, and asking for help is a courageous step.',
                'author': 'Mariska Hargitay',
                'category': 'hope',
                'is_active': True
            },
            {
                'quote': 'Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.',
                'author': 'Unknown',
                'category': 'happiness',
                'is_active': True
            },
            {
                'quote': 'It\'s okay to not be okay. It\'s okay to ask for help. It\'s okay to take time for yourself.',
                'author': 'Unknown',
                'category': 'peace',
                'is_active': True
            },
            {
                'quote': 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
                'author': 'Nelson Mandela',
                'category': 'resilience',
                'is_active': True
            },
            {
                'quote': 'You are not your illness. You have an individual story to tell. You have a name, a history, a personality. Staying yourself is part of the battle.',
                'author': 'Julian Seifter',
                'category': 'strength',
                'is_active': True
            },
            {
                'quote': 'Start where you are. Use what you have. Do what you can.',
                'author': 'Arthur Ashe',
                'category': 'motivation',
                'is_active': True
            },
            {
                'quote': 'What mental health needs is more sunlight, more candor, and more unashamed conversation.',
                'author': 'Glenn Close',
                'category': 'inspiration',
                'is_active': True
            },
            {
                'quote': 'The only journey is the one within.',
                'author': 'Rainer Maria Rilke',
                'category': 'peace',
                'is_active': True
            },
            {
                'quote': 'There is hope, even when your brain tells you there isn\'t.',
                'author': 'John Green',
                'category': 'hope',
                'is_active': True
            },
            {
                'quote': 'Your present circumstances don\'t determine where you can go; they merely determine where you start.',
                'author': 'Nido Qubein',
                'category': 'resilience',
                'is_active': True
            },
            {
                'quote': 'Self-care is how you take your power back.',
                'author': 'Lalah Delia',
                'category': 'happiness',
                'is_active': True
            },
            {
                'quote': 'Sometimes the bravest thing you can do is ask for help.',
                'author': 'Unknown',
                'category': 'strength',
                'is_active': True
            },
        ]
        
        quote_count = 0
        for quote_data in quotes_data:
            quote, created = MotivationalQuote.objects.get_or_create(
                quote=quote_data['quote'],
                defaults=quote_data
            )
            if created:
                quote_count += 1
                self.stdout.write(f"  Created quote: {quote.quote[:50]}...")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {quote_count} quotes'))
        
        # Summary
        total_activities = Activity.objects.filter(is_active=True).count()
        total_quotes = MotivationalQuote.objects.filter(is_active=True).count()
        
        self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Total Activities: {total_activities}'))
        self.stdout.write(self.style.SUCCESS(f'Total Quotes: {total_quotes}'))
        self.stdout.write(self.style.SUCCESS('\nSample data loaded successfully!'))