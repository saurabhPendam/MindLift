"""
Groq API Integration Service - Clean Version (No Branding)
File: chatbot/groq_service.py
"""
import os
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache
from groq import Groq

logger = logging.getLogger(__name__)


class YouTubeService:
    """Service to fetch mental health videos from YouTube Data API"""
    
    def __init__(self):
        self.api_key = os.getenv("YOUTUBE_API_KEY") or getattr(settings, "YOUTUBE_API_KEY", None)
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        # Mental health video topics
        self.video_topics = {
            'anxiety': ['anxiety relief', 'calm anxiety', 'anxiety breathing'],
            'depression': ['depression help', 'mood boost', 'overcoming depression'],
            'stress': ['stress relief', 'stress management', 'reduce stress'],
            'meditation': ['guided meditation', 'mindfulness meditation', 'meditation for beginners'],
            'breathing': ['breathing exercises', 'deep breathing', 'box breathing'],
            'sleep': ['sleep meditation', 'sleep relaxation', 'insomnia help'],
            'panic': ['panic attack help', 'grounding techniques', 'panic relief'],
        }
    
    def search_video(self, topic: str, max_results: int = 1, allow_fallback: bool = True) -> Optional[Dict]:
        """Search for mental health videos on YouTube"""
        if not self.api_key:
            logger.warning("YouTube API key not configured")
            return self._get_fallback_video(topic) if allow_fallback else None
        
        search_terms = self.video_topics.get(topic.lower(), [topic])
        query = f"mental health {search_terms[0]}"
        
        # Check cache
        cache_key = f'youtube_video_{topic}'
        cached_video = cache.get(cache_key)
        if cached_video:
            return cached_video
        
        try:
            import requests
            
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'key': self.api_key,
                'videoEmbeddable': 'true',
                'safeSearch': 'strict',
                'relevanceLanguage': 'en',
                'videoDuration': 'medium',
                'order': 'relevance'
            }
            
            response = requests.get(f"{self.base_url}/search", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('items'):
                    video = data['items'][0]
                    video_id = video['id']['videoId']
                    
                    video_info = {
                        'video_id': video_id,
                        'embed_url': f"https://www.youtube.com/embed/{video_id}",
                        'watch_url': f"https://www.youtube.com/watch?v={video_id}",
                        'title': video['snippet']['title'],
                        'description': video['snippet']['description'][:200],
                        'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                        'has_video': True
                    }
                    
                    cache.set(cache_key, video_info, 86400)
                    logger.info(f"✅ Found YouTube video for topic: {topic}")
                    return video_info
            else:
                logger.error(f"YouTube API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"YouTube search error: {str(e)}")
        
        return self._get_fallback_video(topic) if allow_fallback else None
    
    def _get_fallback_video(self, topic: str) -> Optional[Dict]:
        """Fallback to curated videos when API is unavailable"""
        
        fallback_videos = {
            'anxiety': {
                'video_id': 'tybOi4hjZFQ',
                'embed_url': 'https://www.youtube.com/embed/tybOi4hjZFQ',
                'watch_url': 'https://www.youtube.com/watch?v=tybOi4hjZFQ',
                'title': 'Anxiety Relief - 5 Minute Breathing Exercise',
                'description': 'Quick breathing exercise to reduce anxiety',
                'has_video': True
            },
            'stress': {
                'video_id': '92i5m3tV5XY',
                'embed_url': 'https://www.youtube.com/embed/92i5m3tV5XY',
                'watch_url': 'https://www.youtube.com/watch?v=92i5m3tV5XY',
                'title': 'Stress Relief Exercise',
                'description': 'Guided stress management techniques',
                'has_video': True
            },
            'meditation': {
                'video_id': 'ZToicYcHIOU',
                'embed_url': 'https://www.youtube.com/embed/ZToicYcHIOU',
                'watch_url': 'https://www.youtube.com/watch?v=ZToicYcHIOU',
                'title': '10 Minute Guided Meditation',
                'description': 'Calm your mind with this meditation',
                'has_video': True
            },
            'sleep': {
                'video_id': '1vkjQQyu1xo',
                'embed_url': 'https://www.youtube.com/embed/1vkjQQyu1xo',
                'watch_url': 'https://www.youtube.com/watch?v=1vkjQQyu1xo',
                'title': 'Sleep Meditation',
                'description': 'Guided meditation for better sleep',
                'has_video': True
            }
        }
        
        return fallback_videos.get(topic.lower())


class GroqService:
    """AI service for natural conversation - Clean version without branding"""
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE
        self.max_tokens = settings.GROQ_MAX_TOKENS
        self.youtube_service = YouTubeService()
        
        if not self.api_key:
            logger.error("❌ API key not configured!")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"✅ AI service initialized")
        
        # Crisis keywords
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 
            'hurt myself', 'self-harm', 'cutting', 'overdose',
            'no reason to live', 'better off dead', 'end my life'
        ]
        
        # System prompt - NO BRANDING
        self.system_prompt = """You are MindLift, a compassionate mental health companion AI. 

**CORE PRINCIPLES:**
1. Listen empathetically and validate feelings
2. Provide emotional support and encouragement
3. Suggest coping strategies (breathing, meditation, activities)
4. Recommend professional help when needed
5. NEVER diagnose conditions or prescribe medication
6. Always prioritize user safety

**VIDEO SUGGESTIONS:**
When appropriate, suggest helpful videos by mentioning topics:
- For anxiety: "breathing exercises" or "anxiety relief"
- For stress: "stress management" or "relaxation"
- For sleep: "sleep meditation"
- For wellness: "meditation" or "mindfulness"

**RESPONSE STYLE:**
- Warm, empathetic, and non-judgmental
- Concise (2-4 sentences typically)
- Encouraging and supportive
- End with open-ended questions when appropriate
- If user mentions crisis keywords, provide immediate help resources

**CRISIS PROTOCOL:**
If user shows signs of self-harm or suicide:
1. Express immediate concern
2. Provide crisis hotlines (988, 741741, 911)
3. Encourage professional help
4. Stay supportive

Remember: You're a supportive companion, NOT a therapist or doctor."""

    def check_health(self) -> Dict[str, any]:
        """Check if AI service is available"""
        cache_key = 'ai_health_status'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        if not self.client:
            result = {
                'available': False,
                'error': 'AI service not configured',
                'model': None
            }
        else:
            try:
                result = {
                    'available': True,
                    'model': self.model,
                    'temperature': self.temperature,
                    'max_tokens': self.max_tokens
                }
            except Exception as e:
                result = {
                    'available': False,
                    'error': str(e),
                    'model': self.model
                }
        
        cache.set(cache_key, result, 60)
        return result
    
    def _is_crisis_message(self, message: str) -> bool:
        """Check if message contains crisis indicators"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.crisis_keywords)
    
    def _detect_video_topic(self, message: str) -> Optional[str]:
        """Detect if message suggests a video topic"""
        message_lower = message.lower()
        
        topic_keywords = {
            'anxiety': ['anxious', 'anxiety', 'worried', 'nervous', 'panic'],
            'stress': ['stress', 'stressed', 'overwhelmed', 'pressure'],
            'meditation': ['meditate', 'meditation', 'mindfulness', 'calm'],
            'breathing': ['breath', 'breathing', 'breathe'],
            'sleep': ['sleep', 'insomnia', 'tired', 'rest'],
            'depression': ['sad', 'depressed', 'down', 'hopeless']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic
        
        return None
    
    def _get_crisis_response(self) -> str:
        """Get crisis intervention response"""
        return """🚨 **IMMEDIATE HELP AVAILABLE** 🚨

I'm very concerned about your safety. Please contact emergency services immediately:

📞 **National Suicide Prevention Lifeline: 988**
📱 **Crisis Text Line: Text HOME to 741741**
🚨 **Emergency: 911**

You're not alone. These services are available 24/7 with trained professionals who want to help you. Your life matters."""
    
    def send_message(self, message: str, context: Optional[List[Dict]] = None, allow_video: bool = True) -> Dict:
        """
        Send message to AI service
        
        Returns:
            Dict with response data including video information
        """
        # Crisis check
        if self._is_crisis_message(message):
            logger.warning("🚨 CRISIS MESSAGE DETECTED")
            return {
                'text': self._get_crisis_response(),
                'video': None,
                'model': 'crisis_protocol',
                'source': 'crisis_intervention',
                'success': True,
                'safety_flag': 'crisis'
            }
        
        # Check API availability
        if not self.client:
            logger.error("❌ AI client not available")
            return self._get_fallback_response(message)
        
        try:
            # Build conversation
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add context
            if context:
                max_context = settings.MAX_CONTEXT_MESSAGES
                for msg in context[-max_context:]:
                    role = "user" if msg['sender'] == 'user' else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg['content'][:500]
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            logger.info(f"📤 Sending to AI: {len(messages)} messages")
            
            # Call AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.9,
                stream=False
            )
            
            # Extract response
            bot_response = response.choices[0].message.content.strip()
            
            # Detect video topic (only when allowed)
            video_topic = self._detect_video_topic(message) if allow_video else None
            video_info = None
            
            if video_topic:
                video_info = self.youtube_service.search_video(video_topic, allow_fallback=True)
                logger.info(f"🎥 Video suggested for: {video_topic}")
            
            logger.info(f"✅ Response received ({len(bot_response)} chars)")
            
            return {
                'text': bot_response,
                'video': video_info,
                'model': self.model,
                'source': 'ai',
                'success': True,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            logger.error(f"💥 AI API error: {str(e)}")
            return self._get_fallback_response(message, allow_video=allow_video)
    
    def _get_fallback_response(self, message: str, allow_video: bool = True) -> Dict:
        """Rule-based fallback response"""
        message_lower = message.lower()
        video_info = None
        
        # Anxiety
        if any(word in message_lower for word in ['anxious', 'anxiety', 'worried', 'nervous', 'panic']):
            text = "I hear you're feeling anxious. That's really tough. Try this breathing exercise - breathe in for 4 counts, hold for 4, and breathe out for 4. Repeat a few times. How are you feeling now?"
            video_info = self.youtube_service.search_video('anxiety', allow_fallback=True) if allow_video else None
        
        # Depression/Sadness
        elif any(word in message_lower for word in ['sad', 'depressed', 'down', 'unhappy', 'hopeless']):
            text = "I'm sorry you're feeling this way. Your feelings are valid. Would you like to talk about what's been weighing on your mind? I'm here to listen."
            video_info = None
        
        # Stress
        elif any(word in message_lower for word in ['stress', 'stressed', 'overwhelmed', 'pressure']):
            text = "Stress can be really challenging. Here's a technique that might help. Remember to take things one step at a time. What's causing you the most stress right now?"
            video_info = self.youtube_service.search_video('stress', allow_fallback=True) if allow_video else None
        
        # Sleep
        elif any(word in message_lower for word in ['sleep', 'insomnia', 'tired', 'rest']):
            text = "Sleep issues can really affect your well-being. Would a guided sleep meditation help? I'm here to support you."
            video_info = self.youtube_service.search_video('sleep', allow_fallback=True) if allow_video else None
        
        # Greeting
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            text = "Hello! I'm MindLift, here to support you. How are you feeling today? 💙"
            video_info = None
        
        # Default
        else:
            text = "I'm here to listen and support you. Can you tell me more about what's on your mind? How are you feeling right now?"
            video_info = None
        
        return {
            'text': text,
            'video': video_info,
            'model': 'rule_based',
            'source': 'fallback',
            'success': True
        }


# Initialize service
groq_service = GroqService()