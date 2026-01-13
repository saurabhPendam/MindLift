"""
RASA Integration Service
Handles communication between Django and RASA
"""

import requests
import json
import logging
import re
from typing import Dict, List
from django.conf import settings

logger = logging.getLogger(__name__)


class RasaService:
    """Service to interact with RASA server"""
    
    def __init__(self):
        self.rasa_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        self.webhook_url = f"{self.rasa_url}/webhooks/rest/webhook"
        self.timeout = 30
    
    def send_message(self, message: str, sender_id: str) -> List[Dict]:
        """
        Send message to RASA and get response
        
        Args:
            message: User message text
            sender_id: Unique identifier for the user
        
        Returns:
            List of response dictionaries from RASA
        """
        try:
            payload = {
                "sender": sender_id,
                "message": message
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RASA error: {response.status_code} - {response.text}")
                return self._get_error_response()
                
        except requests.exceptions.ConnectionError:
            logger.error("Could not connect to RASA server")
            return self._get_fallback_response()
        
        except requests.exceptions.Timeout:
            logger.error("RASA request timeout")
            return self._get_fallback_response()
        
        except Exception as e:
            logger.error(f"RASA error: {str(e)}")
            return self._get_error_response()
    
    def _get_error_response(self) -> List[Dict]:
        """Return error response"""
        return [{
            "text": "I'm having trouble connecting right now. Please try again in a moment."
        }]
    
    def _get_fallback_response(self) -> List[Dict]:
        """Return fallback response when RASA is unavailable"""
        return [{
            "text": "I'm here to listen. The AI service is temporarily unavailable, but you can still talk to me. Your messages are being saved."
        }]
    
    def check_health(self) -> bool:
        """Check if RASA server is running"""
        try:
            response = requests.get(f"{self.rasa_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False


class MessageProcessor:
    """Process RASA responses and extract special content"""
    
    @staticmethod
    def process_responses(responses: List[Dict]) -> List[Dict]:
        """
        Process RASA responses and extract metadata
        
        Args:
            responses: List of response dicts from RASA
        
        Returns:
            Processed responses with extracted metadata
        """
        processed = []
        
        for response in responses:
            text = response.get('text', '')
            
            # Extract YouTube URL from text
            youtube_url = MessageProcessor.extract_youtube_from_text(text)
            
            # Remove URL from text for cleaner display
            if youtube_url:
                text = MessageProcessor.remove_url_from_text(text)
            
            processed_response = {
                'text': text.strip(),
                'image': response.get('image'),
                'buttons': response.get('buttons', []),
                'custom': response.get('custom', {}),
                'youtube_url': youtube_url,
                'attachment': response.get('attachment')
            }
            
            # Handle custom payloads
            custom = response.get('custom', {})
            if custom.get('youtube'):
                processed_response['youtube_url'] = custom['youtube']
            
            if custom.get('activity'):
                processed_response['activity'] = custom['activity']
            
            if custom.get('quote'):
                processed_response['quote'] = custom['quote']
            
            processed.append(processed_response)
        
        return processed
    
    @staticmethod
    def extract_youtube_from_text(text: str) -> str:
        """Extract YouTube URL from text and convert to embed URL"""
        if not text:
            return None
            
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"
        
        return None
    
    @staticmethod
    def remove_url_from_text(text: str) -> str:
        """Remove URLs from text"""
        if not text:
            return ""
        # Remove YouTube URLs
        url_pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)[^\s]+'
        text = re.sub(url_pattern, '', text)
        # Remove any other URLs
        url_pattern = r'https?://[^\s]+'
        text = re.sub(url_pattern, '', text)
        return text.strip()
    
    @staticmethod
    def create_button_response(text: str, buttons: List[Dict]) -> Dict:
        """Create a button response"""
        return {
            'text': text,
            'buttons': buttons
        }
    
    @staticmethod
    def create_image_response(image_url: str, caption: str = "") -> Dict:
        """Create an image response"""
        return {
            'image': image_url,
            'text': caption
        }


class RasaActionHandler:
    """Handle custom actions from RASA"""
    
    @staticmethod
    def handle_activity_suggestion(user, mood: str = 'low'):
        """Get activity suggestions based on mood"""
        from chatbot.models import Activity
        
        # Map moods to activity categories
        mood_to_category = {
            'low': ['breathing', 'meditation', 'mindfulness'],
            'anxious': ['breathing', 'relaxation', 'meditation'],
            'stressed': ['physical', 'breathing', 'mindfulness'],
            'sad': ['creative', 'social', 'physical']
        }
        
        categories = mood_to_category.get(mood, ['breathing', 'meditation'])
        
        activities = Activity.objects.filter(
            category__in=categories,
            is_active=True
        ).order_by('?')[:3]
        
        return list(activities.values('id', 'title', 'description', 'duration_minutes', 'category'))
    
    @staticmethod
    def handle_quote_request(category: str = None):
        """Get motivational quote"""
        from chatbot.models import MotivationalQuote
        
        query = MotivationalQuote.objects.filter(is_active=True)
        
        if category:
            query = query.filter(category=category)
        
        quote = query.order_by('?').first()
        
        if quote:
            return {
                'id': quote.id,
                'quote': quote.quote,
                'author': quote.author,
                'category': quote.category
            }
        
        return None
    
    @staticmethod
    def handle_report_request(user):
        """Generate sentiment report"""
        from chatbot.sentiment_service import ReportGenerator
        
        generator = ReportGenerator()
        return generator.generate_user_report(user, days=7)


# Initialize service
rasa_service = RasaService()
message_processor = MessageProcessor()
action_handler = RasaActionHandler()