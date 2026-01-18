"""
Optimized LLM Integration Service - MindLift with Performance Improvements
File: chatbot/llm_service.py
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OllamaService:
    """Service to interact with Ollama LLM with performance optimizations"""
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.primary_model = getattr(settings, 'OLLAMA_PRIMARY_MODEL', 'mindlift')
        self.fallback_model = getattr(settings, 'OLLAMA_FALLBACK_MODEL', 'phi')
        # Reduced timeouts for faster fallback
        self.primary_timeout = getattr(settings, 'OLLAMA_PRIMARY_TIMEOUT', 8)
        self.fallback_timeout = getattr(settings, 'OLLAMA_FALLBACK_TIMEOUT', 4)
        
        # Crisis keywords
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die', 
            'hurt myself', 'self-harm', 'cutting', 'overdose',
            'no reason to live', 'better off dead', 'end my life',
            'can\'t go on', 'want to disappear'
        ]
    
    def check_health(self) -> Dict[str, any]:
        """Check if Ollama server is running and models are available"""
        cache_key = 'ollama_health_status'
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code != 200:
                result = {
                    'available': False, 
                    'error': 'Ollama server not responding',
                    'primary_available': False,
                    'fallback_available': False
                }
            else:
                data = response.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                
                primary_available = any(self.primary_model in m for m in models)
                fallback_available = any(self.fallback_model in m for m in models)
                
                result = {
                    'available': True,
                    'primary_available': primary_available,
                    'fallback_available': fallback_available,
                    'installed_models': models,
                    'primary_model': self.primary_model,
                    'fallback_model': self.fallback_model
                }
            
            cache.set(cache_key, result, 30)
            return result
            
        except requests.exceptions.ConnectionError:
            result = {
                'available': False, 
                'error': 'Cannot connect to Ollama. Is it running?',
                'primary_available': False,
                'fallback_available': False
            }
            cache.set(cache_key, result, 10)
            return result
        except Exception as e:
            result = {
                'available': False, 
                'error': f'Error: {str(e)}',
                'primary_available': False,
                'fallback_available': False
            }
            cache.set(cache_key, result, 10)
            return result
    
    def _is_crisis_message(self, message: str) -> bool:
        """Check if message contains crisis indicators"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.crisis_keywords)
    
    def send_message(self, message: str, context: Optional[List[Dict]] = None, use_fallback: bool = False) -> Dict:
        """
        Send message to Ollama with optimizations
        """
        # CRISIS CHECK
        if self._is_crisis_message(message):
            logger.warning("🚨 CRISIS MESSAGE DETECTED")
            return {
                'text': "🚨 **IMMEDIATE HELP AVAILABLE** 🚨\n\nI'm very concerned about your safety. Please contact emergency services immediately:\n\n📞 National Suicide Prevention Lifeline: 988\n📱 Crisis Text Line: Text HOME to 741741\n🚨 Emergency: 911\n\nYou're not alone. Help is available 24/7.",
                'youtube_url': None,
                'model': 'crisis_protocol',
                'source': 'crisis_intervention',
                'success': True
            }
        
        # Select model
        if use_fallback:
            model = self.fallback_model
            timeout = self.fallback_timeout
            logger.info(f"🔄 Using fallback: {model}")
        else:
            model = self.primary_model
            timeout = self.primary_timeout
            logger.info(f"🤖 Using primary: {model}")
        
        try:
            # Build minimal context (only last 2 messages for speed)
            messages = []
            if context:
                for msg in context[-2:]:  # Reduced from 4 to 2
                    messages.append({
                        "role": "user" if msg['sender'] == 'user' else "assistant",
                        "content": msg['content'][:150]  # Reduced from 200 to 150
                    })
            
            messages.append({"role": "user", "content": message})
            
            prompt = self._build_prompt(messages)
            
            # Optimized payload
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,  # Slightly higher for more natural responses
                    "top_p": 0.9,
                    "num_predict": 100,  # Reduced from 150
                    "num_ctx": 1024,     # Reduced context window for speed
                    "repeat_penalty": 1.1
                }
            }
            
            logger.info(f"📤 Sending to {model} (timeout: {timeout}s)")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data.get('response', '').strip()
                
                # Extract video URLs
                video_url = self._extract_youtube_url(bot_response)
                if video_url:
                    bot_response = self._remove_url_from_text(bot_response)
                
                logger.info(f"✅ {model} responded")
                
                return {
                    'text': bot_response,
                    'youtube_url': video_url,
                    'model': model,
                    'source': 'ollama',
                    'success': True
                }
            else:
                logger.error(f"❌ Ollama error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ {model} timeout after {timeout}s")
            return None
        
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 Cannot connect to Ollama")
            return None
        
        except Exception as e:
            logger.error(f"💥 Ollama error: {str(e)}")
            return None
    
    def _build_prompt(self, messages: List[Dict]) -> str:
        """Build optimized prompt"""
        prompt_parts = []
        
        for msg in messages:
            role = msg['role']
            content = msg['content']
            
            if role == 'user':
                prompt_parts.append(f"User: {content}")
            else:
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _extract_youtube_url(self, text: str) -> Optional[str]:
        """Extract YouTube URL from text"""
        import re
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"
        
        return None
    
    def _remove_url_from_text(self, text: str) -> str:
        """Remove URLs from text"""
        import re
        url_pattern = r'https?://[^\s]+'
        return re.sub(url_pattern, '', text).strip()


class RasaFallbackService:
    """RASA service for pattern-based responses"""
    
    def __init__(self):
        self.rasa_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        self.webhook_url = f"{self.rasa_url}/webhooks/rest/webhook"
        self.timeout = 10  # Reduced from 15
    
    def check_health(self) -> bool:
        """Check if RASA server is running"""
        cache_key = 'rasa_health_status'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        try:
            response = requests.get(f"{self.rasa_url}/", timeout=2)
            result = response.status_code == 200
            cache.set(cache_key, result, 30)
            return result
        except:
            cache.set(cache_key, False, 10)
            return False
    
    def send_message(self, message: str, sender_id: str) -> List[Dict]:
        """Send message to RASA"""
        try:
            payload = {"sender": sender_id, "message": message}
            
            logger.info("📤 Sending to RASA")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                responses = response.json()
                logger.info(f"✅ RASA: {len(responses)} messages")
                return responses
            else:
                logger.error(f"❌ RASA error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"💥 RASA error: {str(e)}")
            return []


class HybridLLMService:
    """
    Optimized hybrid service:
    1. MindLift (8s timeout)
    2. Phi (4s timeout)
    3. RASA (10s timeout)
    4. Rule-based
    """
    
    def __init__(self):
        self.ollama = OllamaService()
        self.rasa = RasaFallbackService()
        self.use_ollama = getattr(settings, 'USE_OLLAMA', True)
    
    def get_status(self) -> Dict:
        """Get status of all services"""
        ollama_status = self.ollama.check_health()
        rasa_status = self.rasa.check_health()
        
        return {
            'ollama': ollama_status,
            'rasa': {'available': rasa_status},
            'primary_service': 'ollama_mindlift' if self.use_ollama else 'rasa'
        }
    
    def send_message(self, message: str, sender_id: str, context: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Send message with fast cascading fallback
        """
        logger.info(f"🎯 Processing: {message[:50]}...")
        
        # Try MindLift
        if self.use_ollama:
            ollama_health = self.ollama.check_health()
            
            if ollama_health.get('available') and ollama_health.get('primary_available'):
                logger.info("🤖 Trying primary (MindLift)")
                response = self.ollama.send_message(message, context, use_fallback=False)
                
                if response and response.get('success'):
                    return [response]
                else:
                    logger.warning("⚠️ MindLift timeout, trying Phi")
            
            # Try Phi
            if ollama_health.get('available') and ollama_health.get('fallback_available'):
                logger.info("🔄 Trying fallback (Phi)")
                response = self.ollama.send_message(message, context, use_fallback=True)
                
                if response and response.get('success'):
                    return [response]
                else:
                    logger.warning("⚠️ Phi timeout, trying RASA")
        
        # Try RASA
        if self.rasa.check_health():
            logger.info("🤖 Using RASA")
            rasa_responses = self.rasa.send_message(message, sender_id)
            
            if rasa_responses:
                processed = []
                for resp in rasa_responses:
                    text = resp.get('text', '')
                    youtube_url = self._extract_youtube_url(text)
                    
                    if youtube_url:
                        text = self._remove_url_from_text(text)
                    
                    processed.append({
                        'text': text,
                        'youtube_url': youtube_url,
                        'model': 'rasa',
                        'source': 'rasa',
                        'success': True
                    })
                
                return processed
        
        # Final fallback
        logger.warning("⚠️ Using rule-based fallback")
        return self._get_rule_based_response(message)
    
    def _get_rule_based_response(self, message: str) -> List[Dict]:
        """Enhanced rule-based responses"""
        message_lower = message.lower()
        
        # Greeting
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return [{
                'text': "Hello! I'm MindLift, here to support you. How are you feeling today? 💙",
                'youtube_url': None,
                'model': 'rule_based',
                'source': 'fallback',
                'success': True
            }]
        
        # Anxiety
        if any(word in message_lower for word in ['anxious', 'anxiety', 'worried', 'nervous', 'panic']):
            return [{
                'text': "I hear you're feeling anxious. That's really tough. Try this breathing exercise - it can help calm your nervous system. Take a deep breath in for 4 counts, hold for 4, and breathe out for 4. Repeat a few times.",
                'youtube_url': 'https://www.youtube.com/embed/tybOi4hjZFQ',
                'model': 'rule_based',
                'source': 'fallback',
                'success': True
            }]
        
        # Depression/Sadness
        if any(word in message_lower for word in ['sad', 'depressed', 'down', 'unhappy', 'hopeless', 'empty']):
            return [{
                'text': "I'm sorry you're feeling this way. Your feelings are valid, and it's okay to not be okay. Would you like to talk about what's been weighing on your mind? I'm here to listen.",
                'youtube_url': None,
                'model': 'rule_based',
                'source': 'fallback',
                'success': True
            }]
        
        # Stress
        if any(word in message_lower for word in ['stress', 'stressed', 'overwhelmed', 'pressure', 'too much']):
            return [{
                'text': "Stress can be really challenging. Here's a quick stress-relief technique that might help. Remember to take things one step at a time - you don't have to handle everything at once.",
                'youtube_url': 'https://www.youtube.com/embed/92i5m3tV5XY',
                'model': 'rule_based',
                'source': 'fallback',
                'success': True
            }]
        
        # Loneliness
        if any(word in message_lower for word in ['lonely', 'alone', 'isolated', 'no friends', 'nobody']):
            return [{
                'text': "Feeling lonely is really difficult, and I want you to know that you're not alone in feeling this way. Many people experience loneliness. Have you considered reaching out to someone you trust, or would you like suggestions for connecting with others?",
                'youtube_url': None,
                'model': 'rule_based',
                'source': 'fallback',
                'success': True
            }]
        
        # Default
        return [{
            'text': "I'm here to listen and support you. Can you tell me more about what's on your mind? How are you feeling right now? 💭",
            'youtube_url': None,
            'model': 'rule_based',
            'source': 'fallback',
            'success': True
        }]
    
    def _extract_youtube_url(self, text: str) -> Optional[str]:
        """Extract YouTube URL"""
        import re
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"
        
        return None
    
    def _remove_url_from_text(self, text: str) -> str:
        """Remove URLs"""
        import re
        url_pattern = r'https?://[^\s]+'
        return re.sub(url_pattern, '', text).strip()


# Initialize service
llm_service = HybridLLMService()