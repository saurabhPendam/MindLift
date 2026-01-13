"""
RASA Custom Actions
These actions connect RASA with Django backend
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests
import random


# Django API endpoint (update this with your actual URL)
DJANGO_API_URL = "http://localhost:8000/api"


class ActionSuggestActivity(Action):
    """Suggest activities based on user mood"""

    def name(self) -> Text:
        return "action_suggest_activity"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get user's last intent to determine mood
        intent = tracker.latest_message.get('intent', {}).get('name')
        
        # Map intents to moods
        mood_mapping = {
            'anxious': 'anxious',
            'mood_unhappy': 'low',
            'stress': 'stressed',
            'lonely': 'sad'
        }
        
        mood = mood_mapping.get(intent, 'low')
        
        # Activities based on mood
        activities = {
            'anxious': [
                {
                    'title': '5-Minute Breathing Exercise',
                    'description': 'Deep breathing to calm anxiety',
                    'video': 'https://www.youtube.com/watch?v=tybOi4hjZFQ'
                },
                {
                    'title': 'Progressive Muscle Relaxation',
                    'description': 'Systematically tense and relax muscle groups',
                    'video': 'https://www.youtube.com/watch?v=ClqPtWzozXs'
                }
            ],
            'low': [
                {
                    'title': 'Mood-Boosting Walk',
                    'description': '15-minute outdoor walk',
                    'video': 'https://www.youtube.com/watch?v=CZTAjfJ8umA'
                },
                {
                    'title': 'Uplifting Music Therapy',
                    'description': 'Listen to mood-boosting music',
                    'video': 'https://www.youtube.com/watch?v=2OEL4P1Rz04'
                }
            ],
            'stressed': [
                {
                    'title': 'Quick Stress Relief',
                    'description': '10-minute stress reduction exercise',
                    'video': 'https://www.youtube.com/watch?v=92i5m3tV5XY'
                },
                {
                    'title': 'Yoga for Stress',
                    'description': 'Gentle yoga poses for relaxation',
                    'video': 'https://www.youtube.com/watch?v=COp7BR_Dvps'
                }
            ]
        }
        
        suggested = activities.get(mood, activities['low'])
        activity = random.choice(suggested)
        
        message = f"Here's an activity that might help: **{activity['title']}**\n\n"
        message += f"{activity['description']}\n\n"
        
        if activity.get('video'):
            message += f"{activity['video']}"
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionProvideQuote(Action):
    """Provide motivational quote"""

    def name(self) -> Text:
        return "action_provide_quote"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        quotes = [
            {
                'quote': 'You are braver than you believe, stronger than you seem, and smarter than you think.',
                'author': 'A.A. Milne'
            },
            {
                'quote': 'Mental health is not a destination, but a process. It\'s about how you drive, not where you\'re going.',
                'author': 'Noam Shpancer'
            },
            {
                'quote': 'You don\'t have to control your thoughts. You just have to stop letting them control you.',
                'author': 'Dan Millman'
            },
            {
                'quote': 'Healing takes time, and asking for help is a courageous step.',
                'author': 'Mariska Hargitay'
            },
            {
                'quote': 'Your mental health is a priority. Your happiness is essential. Your self-care is a necessity.',
                'author': 'Unknown'
            },
            {
                'quote': 'It\'s okay to not be okay. It\'s okay to ask for help. It\'s okay to take time for yourself.',
                'author': 'Unknown'
            },
            {
                'quote': 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
                'author': 'Nelson Mandela'
            },
            {
                'quote': 'You are not your illness. You have an individual story to tell. You have a name, a history, a personality. Staying yourself is part of the battle.',
                'author': 'Julian Seifter'
            },
            {
                'quote': 'Start where you are. Use what you have. Do what you can.',
                'author': 'Arthur Ashe'
            },
            {
                'quote': 'What mental health needs is more sunlight, more candor, and more unashamed conversation.',
                'author': 'Glenn Close'
            }
        ]
        
        quote = random.choice(quotes)
        
        message = f"✨ **{quote['quote']}**\n\n— {quote['author']}"
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionGenerateReport(Action):
    """Generate sentiment analysis report"""

    def name(self) -> Text:
        return "action_generate_report"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        message = "I can generate a detailed sentiment analysis report for you! "
        message += "This report will include:\n\n"
        message += "📊 Overall sentiment analysis\n"
        message += "📈 Emotional trends over time\n"
        message += "💡 Personalized recommendations\n"
        message += "🎯 Top emotions detected\n\n"
        message += "Click the 'Generate Report' button in the chat interface to create your report."
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionProvideCrisisResources(Action):
    """Provide crisis intervention resources"""

    def name(self) -> Text:
        return "action_crisis_resources"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        message = "🚨 **IMMEDIATE HELP AVAILABLE** 🚨\n\n"
        message += "Your safety is the most important thing right now. "
        message += "Please reach out for immediate professional help:\n\n"
        message += "📞 **National Suicide Prevention Lifeline**: 988\n"
        message += "📱 **Crisis Text Line**: Text HOME to 741741\n"
        message += "🚑 **Emergency Services**: 911\n\n"
        message += "These services are available 24/7 and staffed by trained professionals "
        message += "who want to help you. You are not alone."
        
        dispatcher.utter_message(text=message)
        
        return []


class ActionCheckIn(Action):
    """Check in with user after some time"""

    def name(self) -> Text:
        return "action_check_in"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        check_ins = [
            "How are you feeling now?",
            "I wanted to check in - how are things going?",
            "Has anything changed since we last talked?",
            "I'm here if you want to talk more. How are you doing?"
        ]
        
        message = random.choice(check_ins)
        dispatcher.utter_message(text=message)
        
        return []


class ActionRecommendProfessional(Action):
    """Recommend professional help based on severity"""

    def name(self) -> Text:
        return "action_recommend_professional"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        message = "Based on what you've shared, I think talking to a mental health professional could be really helpful. "
        message += "Professional therapists have specialized training and can provide personalized support.\n\n"
        message += "You can connect with licensed professionals through our Doctor Consultation page. "
        message += "Would you like help scheduling an appointment?"
        
        dispatcher.utter_message(text=message)
        
        buttons = [
            {"title": "Yes, connect me", "payload": "/talk_doctor"},
            {"title": "Maybe later", "payload": "/deny"}
        ]
        
        dispatcher.utter_message(text="What would you like to do?", buttons=buttons)
        
        return []


class ActionProvideBreathingGuidance(Action):
    """Provide detailed breathing exercise guidance"""

    def name(self) -> Text:
        return "action_breathing_guidance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        message = "Let's practice breathing together. Follow this simple technique:\n\n"
        message += "**4-4-4 Breathing Exercise:**\n"
        message += "1️⃣ Breathe in slowly through your nose for 4 counts\n"
        message += "2️⃣ Hold your breath for 4 counts\n"
        message += "3️⃣ Breathe out slowly through your mouth for 4 counts\n"
        message += "4️⃣ Repeat 5-10 times\n\n"
        message += "Here's a guided video to help:\n\n"
        message += "https://www.youtube.com/watch?v=tybOi4hjZFQ"
        
        dispatcher.utter_message(text=message)
        
        return []