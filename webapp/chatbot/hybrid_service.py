"""
Enhanced Hybrid Service - COMPLETE FIXED VERSION WITH CBT AND ECFN INTEGRATION
File: chatbot/hybrid_service.py
"""

import logging
import requests
import re
from typing import Dict, List, Optional
from django.conf import settings
from .groq_service import groq_service
from .cbt_service import CBTService
from .ecfn_service import ecfn

logger = logging.getLogger(__name__)


class HybridChatService:
    """Hybrid chatbot service combining RASA intent detection with AI enhancement"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.use_rasa = getattr(settings, 'USE_RASA', True)
        self.rasa_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        self.enhance_with_ai = True
        self.video_intent_map = {
            'anxious': 'anxiety',
            'stress': 'stress',
            'work_stress': 'stress',
            'sleep_issues': 'sleep',
            'ask_breathing': 'breathing',
            'ask_meditation': 'meditation',
            'mood_unhappy': 'depression',
            'lonely': 'depression'
        }
        
    def check_rasa_available(self) -> bool:
        """Check if RASA server is running"""
        try:
            response = requests.get(f"{self.rasa_url}/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"RASA availability check failed: {str(e)}")
            return False
    
    def process_message(self, message: str, user_id: str, context: Optional[List[Dict]] = None, 
                       user=None, enable_ecfn=True) -> Dict:
        """
        Process message through hybrid system with ECFN integration.
        
        Args:
            message: User message text
            user_id: User identifier
            context: Conversation history
            user: Django User object (for ECFN analysis)
            enable_ecfn: Whether to use ECFN advanced analysis
        """
        
        # ECFN Analysis (if enabled and user provided)
        ecfn_analysis = None
        if enable_ecfn and user:
            try:
                # Get recent assessments for ECFN
                from .models import PHQ9Assessment, GAD7Assessment, CBTThoughtRecord, CBTBehavioralActivation
                
                recent_phq9 = PHQ9Assessment.objects.filter(user=user).order_by('-completed_at').first()
                recent_gad7 = GAD7Assessment.objects.filter(user=user).order_by('-completed_at').first()
                
                # Count CBT activities
                thought_records_count = CBTThoughtRecord.objects.filter(user=user, completed=True).count()
                behavioral_activities_count = CBTBehavioralActivation.objects.filter(user=user, completed=True).count()
                total_cbt_activities = thought_records_count + behavioral_activities_count
                
                assessments = {}
                if recent_phq9:
                    assessments['phq9'] = recent_phq9.total_score
                    assessments['phq9_q9'] = recent_phq9.q9_suicidal
                    assessments['depression_severity'] = recent_phq9.severity
                if recent_gad7:
                    assessments['gad7'] = recent_gad7.total_score
                
                cbt_engagement = {
                    'sessions_completed': total_cbt_activities,
                    'thought_records': thought_records_count,
                    'activities': behavioral_activities_count
                }
                
                # Run ECFN analysis
                ecfn_analysis = ecfn.process_message(
                    user=user,
                    message=message,
                    conversation_history=context or [],
                    assessments=assessments if assessments else None,
                    cbt_engagement=cbt_engagement
                )
                
                logger.info(f"🧠 ECFN Analysis Complete: Risk={ecfn_analysis['crisis_assessment']['risk_level']}")
                
                # Handle crisis based on ECFN prediction
                if ecfn_analysis['crisis_assessment']['risk_level'] in ['critical', 'high']:
                    logger.warning("🚨 ECFN CRISIS DETECTED")
                    return self._handle_crisis_with_ecfn(ecfn_analysis)
                
            except Exception as e:
                logger.error(f"ECFN analysis error: {str(e)}")
                ecfn_analysis = None
        
        # Standard crisis check (fallback)
        if self._is_crisis_message(message):
            logger.warning("🚨 CRISIS MESSAGE DETECTED")
            return self._handle_crisis()
        
        # Try RASA first
        rasa_available = self.use_rasa and self.check_rasa_available()
        
        if rasa_available:
            rasa_result = self._try_rasa(message, user_id)
            
            if rasa_result and rasa_result.get('success'):
                intent = rasa_result.get('intent', '')
                confidence = rasa_result.get('confidence', 0)
                
                logger.info(f"✅ RASA Intent: {intent} (confidence: {confidence:.2f})")
                
                if confidence >= self.confidence_threshold:
                    logger.info(f"📊 Using RASA response (high confidence)")
                    
                    if self.enhance_with_ai and self._should_enhance(intent):
                        result = self._enhance_rasa_with_ai(rasa_result, message, context)
                    else:
                        result = self._attach_video_if_applicable(rasa_result)
                    
                    # Attach ECFN metadata
                    if ecfn_analysis:
                        result['ecfn'] = ecfn_analysis
                    
                    return result
                
                logger.info(f"⚠️ Low RASA confidence, using AI")
                ai_result = self._try_ai(message, context, ecfn_analysis)
                
                # Preserve RASA video if AI doesn't have one
                if rasa_result.get('video') and not ai_result.get('video'):
                    ai_result['video'] = rasa_result['video']
                
                return ai_result
        
        logger.info("ℹ️ RASA unavailable, using AI only")
        return self._try_ai(message, context, ecfn_analysis)
    
    def _try_rasa(self, message: str, user_id: str) -> Optional[Dict]:
        """Get response from RASA"""
        try:
            response = requests.post(
                f"{self.rasa_url}/webhooks/rest/webhook",
                json={"sender": user_id, "message": message},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"RASA error: {response.status_code}")
                return None
            
            rasa_responses = response.json()
            
            if not rasa_responses:
                logger.warning("RASA returned empty response")
                return None
            
            parsed = self._parse_rasa_responses(rasa_responses)
            intent_data = self._extract_intent(message, user_id)
            
            result = {
                'text': parsed['text'],
                'video': parsed['video'],
                'source': 'rasa',
                'intent': intent_data.get('intent'),
                'confidence': intent_data.get('confidence', 0),
                'success': True
            }
            
            logger.info(f"✅ RASA processed: intent={result['intent']}, video={bool(result['video'])}")
            if result['video']:
                logger.info(f"🎥 RASA video data: {result['video']}")
            
            return result
            
        except Exception as e:
            logger.error(f"RASA error: {str(e)}", exc_info=True)
            return None
    
    def _parse_rasa_responses(self, responses: List[Dict]) -> Dict:
        """Parse RASA responses and extract text + video"""
        all_text = []
        video = None
        
        for resp in responses:
            text = resp.get('text', '')
            
            if text:
                # Extract YouTube URL from text
                youtube_url = self._extract_youtube_url(text)
                
                if youtube_url:
                    # Remove URL from text for cleaner display
                    text = re.sub(r'https?://(?:www\.)?(?:youtube\.com|youtu\.be)[^\s]+', '', text)
                    text = text.strip()
                    
                    if not video:
                        video = self._create_video_object(youtube_url)
                        if video:
                            logger.info(f"✅ Created video from text URL: {youtube_url}")
                
                if text:
                    all_text.append(text)
            
            # Check custom payload for video
            custom = resp.get('custom', {})
            if custom.get('youtube') and not video:
                video = self._create_video_object(custom['youtube'])
                if video:
                    logger.info(f"✅ Created video from custom payload: {custom['youtube']}")
        
        final_text = '\n\n'.join(all_text) if all_text else 'I understand. How can I help you further?'
        
        return {
            'text': final_text,
            'video': video
        }
    
    def _extract_youtube_url(self, text: str) -> Optional[str]:
        """Extract YouTube URL from text"""
        if not text:
            return None
            
        patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'https?://(?:www\.)?youtube-nocookie\.com/embed/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Return the full URL
                return match.group(0)
        
        return None
    
    def _create_video_object(self, url: str) -> Optional[Dict]:
        """
        Create video object from URL
        Returns a complete video object with all required fields
        """
        if not url:
            logger.warning("_create_video_object: No URL provided")
            return None
        
        logger.info(f"🎬 Creating video object from URL: {url}")
        
        # Extract video ID from various URL formats
        video_id = None
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube-nocookie\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            logger.error(f"❌ Could not extract video ID from: {url}")
            return None
        
        logger.info(f"✅ Created video object for ID: {video_id}")
        
        # Create complete video object
        video_object = {
            'video_id': video_id,
            'embed_url': f'https://www.youtube-nocookie.com/embed/{video_id}',
            'watch_url': f'https://www.youtube.com/watch?v={video_id}',
            'title': 'Recommended Video',
            'has_video': True,
            'source': 'rasa'
        }
        
        logger.info(f"📦 Video object created: {video_object}")
        return video_object
    
    def _extract_intent(self, message: str, user_id: str) -> Dict:
        """Extract intent and confidence from RASA"""
        try:
            response = requests.post(
                f"{self.rasa_url}/model/parse",
                json={"text": message, "sender": user_id},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                intent = data.get('intent', {})
                return {
                    'intent': intent.get('name'),
                    'confidence': intent.get('confidence', 0)
                }
        except Exception as e:
            logger.error(f"Intent extraction error: {str(e)}")
        
        return {'intent': None, 'confidence': 0}
    
    def _should_enhance(self, intent: str) -> bool:
        """Determine if response should be enhanced with AI"""
        skip_enhancement = ['crisis', 'greet', 'goodbye', 'thank', 'bot_challenge']
        return intent not in skip_enhancement if intent else True

    def _should_attach_video(self, intent: Optional[str], confidence: Optional[float]) -> bool:
        """Attach video only when intent is clear and mapped to a video topic"""
        if not intent or confidence is None:
            return False
        if confidence < self.confidence_threshold:
            return False
        if intent == 'crisis':
            return False
        return intent in self.video_intent_map

    def _fetch_video_for_intent(self, intent: str) -> Optional[Dict]:
        """Fetch a YouTube video for a given intent"""
        topic = self.video_intent_map.get(intent)
        if not topic:
            return None
        return groq_service.youtube_service.search_video(topic, allow_fallback=False)

    def _attach_video_if_applicable(self, result: Dict) -> Dict:
        """Attach a YouTube video to the response if intent confidence is high"""
        if result.get('video'):
            return result

        intent = result.get('intent')
        confidence = result.get('confidence')

        if not self._should_attach_video(intent, confidence):
            return result

        video_info = self._fetch_video_for_intent(intent)
        if video_info:
            result['video'] = video_info
            logger.info(f"🎥 YouTube video attached for intent: {intent}")

        return result
    
    def _enhance_rasa_with_ai(self, rasa_result: Dict, message: str, context: Optional[List[Dict]]) -> Dict:
        """Enhance RASA's response with AI while preserving video"""
        try:
            rasa_text = rasa_result.get('text', '')
            rasa_video = rasa_result.get('video')
            
            enhancement_prompt = f"""The user said: "{message}"

Our system detected this as a mental health query. Here's our structured response:

{rasa_text}

Please rewrite this response to be more empathetic, natural, and conversational while keeping the same information. Keep it concise (2-4 sentences). Maintain a warm, supportive tone."""

            ai_response = groq_service.send_message(enhancement_prompt, context=None, allow_video=False)
            
            if ai_response.get('success') and ai_response.get('text'):
                enhanced_text = ai_response['text']
                
                # Preserve RASA video or use AI video
                final_video = rasa_video if rasa_video else ai_response.get('video')
                
                enhanced_result = {
                    'text': enhanced_text,
                    'video': final_video,
                    'source': 'assistant',
                    'intent': rasa_result.get('intent'),
                    'confidence': rasa_result.get('confidence'),
                    'success': True
                }
                
                logger.info(f"✅ Enhanced response with video: {bool(final_video)}")
                if final_video:
                    logger.info(f"🎥 Final video data: {final_video}")
                
                return self._attach_video_if_applicable(enhanced_result)
            
        except Exception as e:
            logger.error(f"Enhancement error: {str(e)}")
        
        # Return original RASA result if enhancement fails
        return rasa_result
    
    def _try_ai(self, message: str, context: Optional[List[Dict]] = None, ecfn_analysis=None) -> Dict:
        """Get response from AI with CBT and ECFN integration"""
        try:
            # Check for CBT-relevant patterns
            cbt_prompt_enhancement = CBTService.get_cbt_prompt_integration(message, context)
            
            # Build enhanced prompt with ECFN insights
            enhanced_message = message
            
            if cbt_prompt_enhancement:
                technique = cbt_prompt_enhancement['technique']
                prompts = cbt_prompt_enhancement['prompts']
                logger.info(f"🧠 CBT technique identified: {technique}")
                
                cbt_guidance = f"\n\nTHERAPEUTIC TECHNIQUE SUGGESTION ({technique}):\n"
                cbt_guidance += "\n".join(f"- {prompt}" for prompt in prompts)
                enhanced_message = f"{message}\n{cbt_guidance}"
            
            # Add ECFN personalization if available
            if ecfn_analysis:
                response_config = ecfn_analysis.get('response_config', {})
                emotion_analysis = ecfn_analysis.get('emotion_analysis', {})
                mood_trajectory = ecfn_analysis.get('mood_trajectory', {})
                
                ecfn_context = "\n\nPERSONALIZATION CONTEXT:\n"
                ecfn_context += f"- User's dominant emotion: {emotion_analysis.get('dominant_emotion', 'unknown')}\n"
                ecfn_context += f"- Mood trend (7-day): {mood_trajectory.get('trend', 'unknown')}\n"
                ecfn_context += f"- Response tone: {response_config.get('tone', 'empathetic')}\n"
                ecfn_context += f"- Suggested techniques: {', '.join(response_config.get('techniques', []))}\n"
                
                enhanced_message += ecfn_context
            
            ai_result = groq_service.send_message(enhanced_message, context, allow_video=False)
            
            result = {
                'text': ai_result.get('text', ''),
                'video': ai_result.get('video'),
                'source': 'assistant',
                'intent': None,
                'confidence': None,
                'success': ai_result.get('success', False),
                'cbt_technique': cbt_prompt_enhancement['technique'] if cbt_prompt_enhancement else None
            }
            
            # Attach ECFN analysis
            if ecfn_analysis:
                result['ecfn'] = {
                    'emotion': ecfn_analysis['emotion_analysis']['dominant_emotion'],
                    'mood_trend': ecfn_analysis['mood_trajectory']['trend'],
                    'crisis_risk': ecfn_analysis['crisis_assessment']['risk_level']
                }
            
            if result['video']:
                logger.info(f"🎥 AI video data: {result['video']}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI error: {str(e)}")
            return self._get_emergency_fallback(message)
    
    def _is_crisis_message(self, message: str) -> bool:
        """Check for crisis keywords"""
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die',
            'hurt myself', 'self-harm', 'cutting', 'overdose',
            'no reason to live', 'better off dead'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in crisis_keywords)
    
    def _handle_crisis(self) -> Dict:
        """Handle crisis situation"""
        return {
            'text': """🚨 **IMMEDIATE HELP AVAILABLE** 🚨

I'm very concerned about your safety. Please contact emergency services immediately:

📞 **National Suicide Prevention Lifeline: 988**
📱 **Crisis Text Line: Text HOME to 741741**
🚨 **Emergency: 911**

You're not alone. These services are available 24/7 with trained professionals who want to help you.""",
            'video': None,
            'source': 'crisis',
            'intent': 'crisis',
            'confidence': 1.0,
            'success': True
        }
    
    def _handle_crisis_with_ecfn(self, ecfn_analysis: Dict) -> Dict:
        """Enhanced crisis handling with ECFN context"""
        crisis_assessment = ecfn_analysis.get('crisis_assessment', {})
        indicators = crisis_assessment.get('indicators', [])
        
        # Build contextual crisis message
        crisis_text = """🚨 **IMMEDIATE HELP AVAILABLE** 🚨

I'm very concerned about your safety. Please contact emergency services immediately:

📞 **National Suicide Prevention Lifeline: 988**
📱 **Crisis Text Line: Text HOME to 741741**
🚨 **Emergency: 911**

"""
        
        # Add specific concerns if available
        if indicators:
            crisis_text += "\n**I noticed:**\n"
            for indicator in indicators[:3]:  # Limit to top 3
                if 'description' in indicator:
                    crisis_text += f"- {indicator['description']}\n"
        
        crisis_text += "\nYou're not alone. These services are available 24/7 with trained professionals who want to help you."
        
        return {
            'text': crisis_text,
            'video': None,
            'source': 'crisis',
            'intent': 'crisis',
            'confidence': 1.0,
            'success': True,
            'ecfn': {
                'risk_score': crisis_assessment.get('risk_score'),
                'risk_level': crisis_assessment.get('risk_level'),
                'indicators_count': len(indicators)
            }
        }
    
    def _get_emergency_fallback(self, message: str) -> Dict:
        """Emergency fallback"""
        return {
            'text': "I'm here to listen and support you. Please tell me more about how you're feeling.",
            'video': None,
            'source': 'assistant',
            'intent': None,
            'confidence': 0,
            'success': True
        }


# Initialize service
hybrid_service = HybridChatService()