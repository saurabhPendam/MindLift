"""
Enhanced Sentiment Analysis Service - COMPLETE FIXED VERSION
File: chatbot/sentiment_service.py
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nrclex import NRCLex
import re
from typing import Dict, Tuple, List
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from chatbot.models import Message, SentimentReport, Conversation
import logging

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Handles sentiment analysis using VADER and NRCLex"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Crisis keywords for safety detection
        self.crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'want to die',
            'hurt myself', 'self-harm', 'cutting', 'overdose',
            'no reason to live', 'better off dead', 'end my life'
        ]
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of text using VADER and NRCLex
        
        Returns:
            dict: {
                'vader': {'compound': float, 'pos': float, 'neu': float, 'neg': float},
                'label': str ('positive', 'negative', 'neutral'),
                'score': float,
                'emotions': dict (NRC emotions),
                'crisis_detected': bool
            }
        """
        # Check for crisis keywords
        crisis_detected = self._check_crisis(text)
        
        # VADER Sentiment Analysis
        vader_scores = self.vader.polarity_scores(text)
        compound = vader_scores['compound']
        
        # Determine sentiment label with stricter thresholds
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        # NRCLex Emotion Analysis
        emotions = {}
        top_emotions = []
        affect_frequencies = {}
        
        try:
            emotion_obj = NRCLex(text)
            emotions = emotion_obj.raw_emotion_scores
            top_emotions = emotion_obj.top_emotions
            affect_frequencies = emotion_obj.affect_frequencies
        except Exception as e:
            logger.error(f"NRCLex error: {e}")
        
        return {
            'vader': vader_scores,
            'label': label,
            'score': compound,
            'emotions': emotions,
            'top_emotions': top_emotions,
            'affect_frequencies': affect_frequencies,
            'crisis_detected': crisis_detected
        }
    
    def _check_crisis(self, text: str) -> bool:
        """Check if message contains crisis indicators"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.crisis_keywords)
    
    def analyze_message(self, message_obj) -> Dict:
        """Analyze a message object and update it with sentiment data"""
        result = self.analyze_text(message_obj.content)
        
        # Update message with sentiment data
        message_obj.sentiment_score = result['score']
        message_obj.sentiment_label = result['label']
        message_obj.emotions = result['emotions']
        message_obj.contains_crisis_keywords = result['crisis_detected']
        
        # Flag for professional referral if severely negative
        if result['score'] < -0.5:
            message_obj.requires_professional_referral = True
        
        message_obj.save()
        
        logger.info(f"Message analyzed: score={result['score']:.3f}, label={result['label']}")
        
        return result
    
    def get_sentiment_label_from_score(self, score: float) -> str:
        """Convert VADER compound score to label"""
        if score >= 0.05:
            return 'positive'
        elif score <= -0.05:
            return 'negative'
        else:
            return 'neutral'


class ReportGenerator:
    """Generate comprehensive sentiment analysis reports"""
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
    
    def generate_conversation_report(self, conversation, user) -> Dict:
        """Generate detailed report for a specific conversation"""
        messages = Message.objects.filter(
            conversation=conversation,
            sender='user'
        ).order_by('timestamp')
        
        if not messages.exists():
            return {
                'error': 'No messages found in this conversation',
                'total_messages': 0
            }
        
        logger.info(f"Generating conversation report for conversation {conversation.id}, {messages.count()} messages")
        
        return self._calculate_detailed_metrics(
            messages, 
            user, 
            conversation=conversation
        )
    
    def generate_user_report(self, user, days=7) -> Dict:
        """Generate report for user's messages over specified days"""
        start_date = datetime.now() - timedelta(days=days)
        
        messages = Message.objects.filter(
            conversation__user=user,
            sender='user',
            timestamp__gte=start_date,
            conversation__is_deleted=False
        ).order_by('timestamp')
        
        if not messages.exists():
            return {
                'error': 'No messages found in this period',
                'total_messages': 0
            }
        
        logger.info(f"Generating user report for {user.username}, {messages.count()} messages")
        
        return self._calculate_detailed_metrics(
            messages, 
            user, 
            days=days
        )
    
    def _calculate_detailed_metrics(self, messages, user, conversation=None, days=None) -> Dict:
        """
        Calculate comprehensive sentiment metrics from messages
        FIXED VERSION with PROPER SCORE CALCULATION
        """
        if not messages.exists():
            return {
                'error': 'No messages found',
                'total_messages': 0
            }
        
        logger.info(f"Calculating metrics for {messages.count()} messages")
        
        # Analyze any messages that don't have sentiment yet
        messages_to_analyze = messages.filter(
            Q(sentiment_score__isnull=True) | Q(sentiment_label__isnull=True)
        )
        
        analyzed_count = 0
        for msg in messages_to_analyze:
            self.analyzer.analyze_message(msg)
            analyzed_count += 1
        
        if analyzed_count > 0:
            logger.info(f"Analyzed {analyzed_count} new messages")
        
        # Refresh queryset to get updated sentiment data
        messages = messages.filter(sentiment_score__isnull=False)
        
        if not messages.exists():
            return {
                'error': 'Unable to analyze messages',
                'total_messages': 0
            }
        
        total = messages.count()
        logger.info(f"Total messages with sentiment: {total}")
        
        # Count sentiments
        positive = messages.filter(sentiment_label='positive').count()
        negative = messages.filter(sentiment_label='negative').count()
        neutral = messages.filter(sentiment_label='neutral').count()
        
        logger.info(f"Sentiment counts - Positive: {positive}, Neutral: {neutral}, Negative: {negative}")
        
        # Calculate percentages
        pos_pct = (positive / total * 100) if total > 0 else 0
        neg_pct = (negative / total * 100) if total > 0 else 0
        neu_pct = (neutral / total * 100) if total > 0 else 0
        
        # CRITICAL FIX: Calculate average sentiment score correctly
        # Get all sentiment scores
        sentiment_scores = list(messages.values_list('sentiment_score', flat=True))
        
        # Log individual scores for debugging
        logger.info(f"Sentiment scores: {sentiment_scores}")
        
        # Calculate average manually to ensure correctness
        if sentiment_scores:
            avg_score = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_score = 0.0
        
        logger.info(f"Calculated average score: {avg_score:.3f}")
        
        # Double-check with Django's Avg (for verification)
        db_avg = messages.aggregate(Avg('sentiment_score'))['sentiment_score__avg']
        if db_avg is not None:
            logger.info(f"Database average score: {db_avg:.3f}")
        else:
            logger.warning("Database average is None")
        
        # Use the manually calculated average as it's more reliable
        final_avg_score = float(avg_score)
        
        # Determine overall sentiment based on average score
        if final_avg_score >= 0.05:
            overall = 'positive'
        elif final_avg_score <= -0.05:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        logger.info(f"Overall sentiment: {overall} (score: {final_avg_score:.3f})")
        
        # Aggregate emotions
        all_emotions = {}
        for msg in messages:
            if msg.emotions:
                for emotion, score in msg.emotions.items():
                    all_emotions[emotion] = all_emotions.get(emotion, 0) + score
        
        # Get top 5 emotions
        sorted_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotions = dict(sorted_emotions[:5]) if sorted_emotions else {}
        
        # === SEMANTIC INSIGHTS AGGREGATION ===
        # Aggregate themes
        all_themes = {}
        for msg in messages:
            if msg.themes:
                for theme, score in msg.themes.items():
                    all_themes[theme] = all_themes.get(theme, 0) + score
        sorted_themes = sorted(all_themes.items(), key=lambda x: x[1], reverse=True)
        top_themes = dict(sorted_themes[:5]) if sorted_themes else {}
        
        # Aggregate cognitive distortions
        all_distortions = {}
        for msg in messages:
            if msg.cognitive_distortions:
                for distortion, patterns in msg.cognitive_distortions.items():
                    all_distortions[distortion] = all_distortions.get(distortion, 0) + len(patterns)
        sorted_distortions = sorted(all_distortions.items(), key=lambda x: x[1], reverse=True)
        top_distortions = dict(sorted_distortions[:5]) if sorted_distortions else {}
        
        # Aggregate coping strategies
        all_coping = {}
        for msg in messages:
            if msg.coping_indicators:
                for strategy in msg.coping_indicators:
                    all_coping[strategy] = all_coping.get(strategy, 0) + 1
        sorted_coping = sorted(all_coping.items(), key=lambda x: x[1], reverse=True)
        top_coping = dict(sorted_coping[:5]) if sorted_coping else {}
        
        # Crisis level statistics
        crisis_immediate = messages.filter(crisis_level='immediate').count()
        crisis_high = messages.filter(crisis_level='high').count()
        crisis_moderate = messages.filter(crisis_level='moderate').count()
        
        # Average linguistic features
        avg_first_person = 0
        avg_negative_ratio = 0
        feature_count = 0
        for msg in messages:
            if msg.linguistic_features:
                if 'first_person_ratio' in msg.linguistic_features:
                    avg_first_person += msg.linguistic_features['first_person_ratio']
                    feature_count += 1
                if 'negative_word_ratio' in msg.linguistic_features:
                    avg_negative_ratio += msg.linguistic_features['negative_word_ratio']
        
        if feature_count > 0:
            avg_first_person /= feature_count
            avg_negative_ratio /= feature_count
        
        semantic_insights = {
            'themes': top_themes,
            'cognitive_distortions': top_distortions,
            'coping_strategies': top_coping,
            'crisis_levels': {
                'immediate': crisis_immediate,
                'high': crisis_high,
                'moderate': crisis_moderate
            },
            'linguistic_patterns': {
                'avg_first_person_ratio': round(avg_first_person, 3),
                'avg_negative_word_ratio': round(avg_negative_ratio, 3)
            }
        }
        
        # FIXED: Calculate sentiment trend with proper list handling
        sentiment_trend = self._calculate_sentiment_trend(messages)
        
        # Identify concerning patterns
        crisis_messages = messages.filter(contains_crisis_keywords=True).count()
        professional_referral_needed = messages.filter(requires_professional_referral=True).count()
        
        # Generate detailed summary
        summary = self._generate_detailed_summary(
            overall=overall,
            avg_score=final_avg_score,
            positive=positive,
            negative=negative,
            neutral=neutral,
            total=total,
            top_emotions=top_emotions,
            trend=sentiment_trend,
            crisis_count=crisis_messages,
            referral_count=professional_referral_needed,
            semantic_insights=semantic_insights
        )
        
        # Generate personalized recommendations
        recommendations = self._generate_recommendations(
            overall, final_avg_score, top_emotions, sentiment_trend, semantic_insights
        )
        
        # Determine date range
        if days:
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
        else:
            start_date = messages.first().timestamp
            end_date = messages.last().timestamp
        
        # Create report object with CORRECT average score
        report = SentimentReport.objects.create(
            user=user,
            conversation=conversation,
            start_date=start_date,
            end_date=end_date,
            overall_sentiment=overall,
            average_score=final_avg_score,  # FIXED: Use the correctly calculated average
            positive_percentage=pos_pct,
            negative_percentage=neg_pct,
            neutral_percentage=neu_pct,
            total_messages=total,
            positive_count=positive,
            negative_count=negative,
            neutral_count=neutral,
            dominant_emotions=top_emotions,
            recommendations=recommendations
        )
        
        logger.info(f"Report created with ID: {report.id}, average_score: {report.average_score:.3f}")
        
        return {
            'report_id': report.id,
            'overall_sentiment': overall,
            'average_score': round(final_avg_score, 3),  # FIXED: Return the correct score
            'total_messages': total,
            'positive': {
                'count': positive,
                'percentage': round(pos_pct, 1)
            },
            'negative': {
                'count': negative,
                'percentage': round(neg_pct, 1)
            },
            'neutral': {
                'count': neutral,
                'percentage': round(neu_pct, 1)
            },
            'top_emotions': top_emotions,
            'sentiment_trend': sentiment_trend,
            'semantic_insights': semantic_insights,
            'safety_flags': {
                'crisis_messages': crisis_messages,
                'professional_referral_needed': professional_referral_needed
            },
            'summary': summary,
            'recommendations': recommendations.split('\n'),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
    
    def _calculate_sentiment_trend(self, messages) -> str:
        """
        Calculate if sentiment is improving, declining, or stable
        FIXED: Properly handle both QuerySet and list types
        """
        # Convert to list if it's a QuerySet
        if hasattr(messages, 'values_list'):
            message_list = list(messages)
        else:
            message_list = list(messages)
        
        if len(message_list) < 3:
            return 'stable'
        
        # Split messages into first half and second half
        mid_point = len(message_list) // 2
        first_half = message_list[:mid_point]
        second_half = message_list[mid_point:]
        
        # Calculate averages for each half
        first_scores = [msg.sentiment_score for msg in first_half if msg.sentiment_score is not None]
        second_scores = [msg.sentiment_score for msg in second_half if msg.sentiment_score is not None]
        
        if not first_scores or not second_scores:
            return 'stable'
        
        first_avg = sum(first_scores) / len(first_scores)
        second_avg = sum(second_scores) / len(second_scores)
        
        diff = second_avg - first_avg
        
        logger.info(f"Trend calculation - First half avg: {first_avg:.3f}, Second half avg: {second_avg:.3f}, Diff: {diff:.3f}")
        
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_detailed_summary(self, overall, avg_score, positive, negative, 
                                   neutral, total, top_emotions, trend, 
                                   crisis_count, referral_count, semantic_insights=None) -> str:
        """Generate a comprehensive text summary of the sentiment analysis"""
        
        summary_parts = []
        
        # Calculate percentages safely
        pos_pct = (positive / total * 100) if total > 0 else 0
        neg_pct = (negative / total * 100) if total > 0 else 0
        neu_pct = (neutral / total * 100) if total > 0 else 0
        
        # Overall sentiment introduction
        if overall == 'positive':
            summary_parts.append(
                f"Your emotional state appears predominantly positive with an average "
                f"sentiment score of {avg_score:.2f}. Out of {total} messages analyzed, "
                f"{positive} ({pos_pct:.1f}%) showed positive sentiment."
            )
        elif overall == 'negative':
            summary_parts.append(
                f"The analysis indicates you've been experiencing challenging emotions, "
                f"with an average sentiment score of {avg_score:.2f}. Out of {total} messages "
                f"analyzed, {negative} ({neg_pct:.1f}%) showed negative sentiment."
            )
        else:
            summary_parts.append(
                f"Your emotional state appears balanced with an average sentiment score "
                f"of {avg_score:.2f}. Out of {total} messages analyzed, you showed a mix "
                f"of emotions."
            )
        
        # Sentiment distribution
        summary_parts.append(
            f"\n\nSentiment Distribution:\n"
            f"• Positive messages: {positive} ({pos_pct:.1f}%)\n"
            f"• Neutral messages: {neutral} ({neu_pct:.1f}%)\n"
            f"• Negative messages: {negative} ({neg_pct:.1f}%)"
        )
        
        # Emotional patterns
        if top_emotions:
            emotion_list = [f"{emotion} ({score:.1f})" for emotion, score in list(top_emotions.items())[:3]]
            summary_parts.append(
                f"\n\nDominant Emotional Themes:\n"
                f"The most prominent emotions detected in your messages were: {', '.join(emotion_list)}."
            )
        
        # Trend analysis
        if trend == 'improving':
            summary_parts.append(
                f"\n\nPositive Trend:\n"
                f"Good news! Your emotional state shows signs of improvement over this period. "
                f"Your recent messages are more positive than earlier ones."
            )
        elif trend == 'declining':
            summary_parts.append(
                f"\n\nConcern Noted:\n"
                f"Your emotional state appears to have declined during this period. "
                f"Recent messages show more negative sentiment than earlier ones. "
                f"This may be a good time to reach out for additional support."
            )
        else:
            summary_parts.append(
                f"\n\nStable Pattern:\n"
                f"Your emotional state has remained relatively consistent throughout this period."
            )
        
        # Safety flags
        if crisis_count > 0 or referral_count > 0:
            summary_parts.append(
                f"\n\n⚠️ Important Note:\n"
            )
            if crisis_count > 0:
                summary_parts.append(
                    f"We detected {crisis_count} message(s) with crisis-related content. "
                    f"Your safety is our priority. Please consider reaching out to a "
                    f"mental health professional or crisis helpline."
                )
            if referral_count > 0:
                summary_parts.append(
                    f"\n{referral_count} message(s) suggested significantly negative emotional states. "
                    f"Professional support may be beneficial."
                )
        
        # Semantic insights summary
        if semantic_insights:
            if semantic_insights.get('themes'):
                theme_list = list(semantic_insights['themes'].keys())[:3]
                if theme_list:
                    summary_parts.append(
                        f"\n\nPrimary Concerns:\n"
                        f"Your conversations primarily focused on: {', '.join(theme_list).replace('_', ' ')}."
                    )
            
            if semantic_insights.get('cognitive_distortions'):
                distortions = list(semantic_insights['cognitive_distortions'].keys())[:3]
                if distortions:
                    summary_parts.append(
                        f"\n\nThinking Patterns:\n"
                        f"Common cognitive patterns detected: {', '.join(distortions).replace('_', ' ')}. "
                        f"CBT exercises can help address these thought patterns."
                    )
            
            if semantic_insights.get('coping_strategies'):
                strategies = list(semantic_insights['coping_strategies'].keys())[:3]
                if strategies:
                    summary_parts.append(
                        f"\n\nPositive Behaviors:\n"
                        f"You mentioned using: {', '.join(strategies)}. Keep up these healthy coping strategies!"
                    )
            
            crisis_levels = semantic_insights.get('crisis_levels', {})
            if crisis_levels.get('immediate', 0) > 0 or crisis_levels.get('high', 0) > 0:
                summary_parts.append(
                    f"\n\n🚨 Crisis Detection:\n"
                    f"Immediate: {crisis_levels.get('immediate', 0)}, High: {crisis_levels.get('high', 0)}. "
                    f"Please seek immediate professional help if you're in crisis."
                )
        
        return "".join(summary_parts)
    
    def _generate_recommendations(self, sentiment: str, score: float, 
                                 emotions: Dict, trend: str, semantic_insights=None) -> str:
        """
        Generate HIGHLY PERSONALIZED recommendations based on user's unique patterns
        Each user gets custom advice based on their specific themes, distortions, and behaviors
        """
        recommendations = []
        
        # Extract user-specific data
        themes = semantic_insights.get('themes', {}) if semantic_insights else {}
        distortions = semantic_insights.get('cognitive_distortions', {}) if semantic_insights else {}
        coping = semantic_insights.get('coping_strategies', {}) if semantic_insights else {}
        crisis_levels = semantic_insights.get('crisis_levels', {}) if semantic_insights else {}
        linguistic = semantic_insights.get('linguistic_patterns', {}) if semantic_insights else {}
        
        # === PERSONALIZED OPENING based on user's primary issues ===
        opening = self._generate_personalized_opening(sentiment, score, themes, distortions, trend)
        recommendations.append(opening)
        
        # === THEME-SPECIFIC RECOMMENDATIONS (Most Important) ===
        theme_recs = self._generate_theme_recommendations(themes, emotions, coping)
        if theme_recs:
            recommendations.append(theme_recs)
        
        # === COGNITIVE DISTORTION INTERVENTIONS (CBT) ===
        distortion_recs = self._generate_distortion_interventions(distortions, themes)
        if distortion_recs:
            recommendations.append(distortion_recs)
        
        # === REINFORCE EXISTING COPING STRATEGIES ===
        coping_recs = self._generate_coping_reinforcement(coping, themes)
        if coping_recs:
            recommendations.append(coping_recs)
        
        # === TREND-BASED ACTION PLANS ===
        trend_recs = self._generate_trend_recommendations(trend, score, themes)
        if trend_recs:
            recommendations.append(trend_recs)
        
        # === COMBINATION ISSUE STRATEGIES ===
        combo_recs = self._generate_combination_strategies(themes, emotions, distortions)
        if combo_recs:
            recommendations.append(combo_recs)
        
        # === CRISIS SUPPORT (if needed) ===
        if crisis_levels.get('immediate', 0) > 0 or crisis_levels.get('high', 0) > 0:
            recommendations.append(
                "\n\n🚨 IMMEDIATE CRISIS SUPPORT:\n"
                "Your messages indicate urgent distress. Please:\n"
                "• Call 988 (Suicide & Crisis Lifeline) - Available 24/7\n"
                "• Text HOME to 741741 (Crisis Text Line)\n"
                "• Call 911 if in immediate danger\n"
                "• Go to nearest emergency room\n"
                "• Tell someone you trust RIGHT NOW\n\n"
                "You don't have to face this alone. Help is available."
            )
        else:
            recommendations.append(
                "\n\n🆘 Support Resources:\n"
                "• 988 Suicide & Crisis Lifeline (24/7)\n"
                "• Text HOME to 741741 (Crisis Text Line)\n"
                "• MindLift Doctor Consultation for professional guidance"
            )
        
        return '\n'.join(recommendations)
    
    def _generate_personalized_opening(self, sentiment, score, themes, distortions, trend):
        """Create personalized opening based on user's specific situation"""
        theme_list = list(themes.keys())[:2] if themes else []
        distortion_list = list(distortions.keys())[:2] if distortions else []
        
        # Build custom opening
        opening_parts = []
        
        if sentiment == 'negative' and score < -0.5:
            opening_parts.append("🔴 Personalized Support Plan for You:")
            if theme_list:
                concerns = ', '.join([t.replace('_', ' ') for t in theme_list])
                opening_parts.append(f"Based on your conversations, you're primarily dealing with {concerns}.")
            if distortion_list:
                patterns = ', '.join([d.replace('_', ' ') for d in distortion_list])
                opening_parts.append(f"I've noticed thinking patterns like {patterns} in your messages.")
        elif sentiment == 'negative':
            opening_parts.append("🟠 Your Personalized Wellness Plan:")
            if theme_list:
                concerns = ', '.join([t.replace('_', ' ') for t in theme_list])
                opening_parts.append(f"You've been talking about {concerns} - let's address these specifically.")
        elif sentiment == 'neutral' and trend == 'declining':
            opening_parts.append("🟡 Early Intervention Plan:")
            opening_parts.append("I've noticed your mood declining. Let's take proactive steps now.")
        elif sentiment == 'neutral':
            opening_parts.append("🟡 Maintaining Your Progress:")
            if theme_list:
                concerns = ', '.join([t.replace('_', ' ') for t in theme_list])
                opening_parts.append(f"You've mentioned {concerns} - here's how to keep managing these effectively.")
        else:  # positive
            opening_parts.append("🟢 Celebrating Your Growth:")
            if theme_list:
                concerns = ', '.join([t.replace('_', ' ') for t in theme_list])
                opening_parts.append(f"You're making progress with {concerns}. Let's build on this success!")
        
        return '\n'.join(opening_parts)
    
    def _generate_theme_recommendations(self, themes, emotions, coping):
        """Generate specific recommendations for each theme the user struggles with"""
        if not themes:
            return None
        
        recs = ["\n\n📋 For Your Specific Concerns:"]
        
        # Anxiety
        if 'anxiety' in themes:
            has_breathing = any('breath' in c for c in coping.keys())
            recs.append(
                f"\nManaging Your Anxiety:\n"
                f"{'• Continue your breathing exercises - they are working!' if has_breathing else '• Start with 4-7-8 breathing: Breathe in 4s, hold 7s, out 8s (do 3-5 cycles)'}\n"
                "• Try the 5-4-3-2-1 grounding: Name 5 things you see, 4 you hear, 3 you feel, 2 you smell, 1 you taste\n"
                "• Schedule 'worry time': Set aside 15 minutes daily to address anxious thoughts\n"
                "• Limit caffeine and alcohol - these amplify anxiety symptoms\n"
                "• Practice saying 'I notice I'm feeling anxious' instead of 'I am anxious'"
            )
        
        # Depression
        if 'depression' in themes:
            has_exercise = any('exercise' in c or 'walk' in c for c in coping.keys())
            recs.append(
                f"\nFor Your Depression:\n"
                f"{'• Keep up your physical activity - even small walks make a huge difference!' if has_exercise else '• Start small: Take a 5-minute walk today, increase by 2 minutes each day'}\n"
                "• Behavioral activation: Do ONE enjoyable activity daily, even if you don't feel like it\n"
                "• Set micro-goals: Instead of 'clean house', start with 'put 3 items away'\n"
                "• Connect with one person daily - even a text message counts\n"
                "• Track small wins: Write down 3 things you accomplished today (no matter how small)"
            )
        
        # Work Stress
        if 'work_stress' in themes:
            recs.append(
                "\nManaging Work-Related Stress:\n"
                "• Use the Pomodoro technique: 25 min focused work, 5 min break\n"
                "• Set boundaries: Define work hours and stick to them\n"
                "• Practice saying no: You can't pour from an empty cup\n"
                "• Take real lunch breaks away from your desk\n"
                "• Sunday planning: List top 3 priorities for the week to reduce overwhelm\n"
                "• Consider talking to your manager about workload if it's consistently unmanageable"
            )
        
        # Sleep Issues
        if 'sleep' in themes:
            recs.append(
                "\nImproving Your Sleep:\n"
                "• Consistent schedule: Same bedtime/wake time (even weekends) for 2 weeks\n"
                "• 10-3-2-1-0 rule: No caffeine 10h before bed, no food 3h, no work 2h, no screens 1h, zero snoozes\n"
                "• If awake >20 min, leave bed and do something boring (don't check phone)\n"
                "• Create sleep ritual: Dim lights, cool room (65-68°F), white noise or fan\n"
                "• Morning sunlight: Get 10-15 minutes of outdoor light within 1 hour of waking\n"
                "• Track your sleep patterns to identify what helps"
            )
        
        # Relationships
        if 'relationships' in themes:
            recs.append(
                "\nFor Relationship Challenges:\n"
                "• Use 'I' statements: 'I feel ___ when ___ because ___' instead of blaming\n"
                "• Practice active listening: Repeat back what you heard before responding\n"
                "• Schedule quality time: Put relationship time in calendar like any important meeting\n"
                "• Express appreciation daily: Tell someone one thing you appreciate about them\n"
                "• Set boundaries clearly: 'I need ___' is okay to say\n"
                "• Consider couples/family counseling if conflicts persist"
            )
        
        # Self-Esteem
        if 'self_esteem' in themes:
            recs.append(
                "\nBuilding Your Self-Esteem:\n"
                "• Write down 5 things you like about yourself (start with anything, even 'I'm breathing')\n"
                "• Challenge self-criticism: Would you say that to a friend? If not, don't say it to yourself\n"
                "• Track accomplishments: Keep a 'wins jar' - write small victories on paper, read when down\n"
                "• Stop comparing: Their Chapter 20 vs your Chapter 1 isn't fair comparison\n"
                "• Affirmations: 'I am enough' - say it even if you don't believe it yet\n"
                "• Celebrate effort, not just results: Trying matters"
            )
        
        # Anger
        if 'anger' in themes:
            recs.append(
                "\nManaging Your Anger:\n"
                "• Pause technique: Count to 10 before responding when angry\n"
                "• Physical release: Intense exercise, punch a pillow, squeeze ice cubes\n"
                "• Identify triggers: Keep anger journal - what happened right before?\n"
                "• Communicate assertively: 'I feel angry when ___ because I need ___'\n"
                "• Time-outs: It's okay to say 'I need a break' and walk away\n"
                "• Address underlying issues: Anger is often covering hurt, fear, or frustration"
            )
        
        # Trauma/PTSD
        if 'trauma' in themes:
            recs.append(
                "\nFor Trauma Recovery:\n"
                "• Grounding techniques: Focus on physical sensations (feet on floor, hands on legs)\n"
                "• Safety plan: Identify safe people, places, and coping tools\n"
                "• EMDR or trauma-focused therapy: Seek specialist for evidence-based treatment\n"
                "• Self-compassion: Healing isn't linear - setbacks are part of recovery\n"
                "• Establish routine: Predictability helps nervous system feel safe\n"
                "• Avoid self-medicating: Alcohol/drugs worsen PTSD long-term"
            )
        
        return '\n'.join(recs)
    
    def _generate_distortion_interventions(self, distortions, themes):
        """Generate CBT interventions for specific cognitive distortions"""
        if not distortions:
            return None
        
        recs = ["\n\n🧠 Challenging Your Thinking Patterns:"]
        
        if 'all_or_nothing' in distortions:
            recs.append(
                "\nAll-or-Nothing Thinking:\n"
                "You tend to see things in extremes. Try this:\n"
                "• When you catch 'always/never', ask: 'Is there a time when this wasn't true?'\n"
                "• Use percentages: Instead of 'I'm a total failure', say 'I succeeded 60% of the time'\n"
                "• Gray thinking: 'Both/and' instead of 'either/or' - Most situations aren't black/white\n"
                "• Example: Change 'I always mess up' to 'I messed up this time, but I've succeeded before'"
            )
        
        if 'catastrophizing' in distortions:
            recs.append(
                "\nCatastrophizing:\n"
                "You jump to worst-case scenarios. Challenge this:\n"
                "• Ask: 'What's the most likely outcome?' (not worst, not best - most likely)\n"
                "• Evidence check: 'How many times has my worst fear actually happened?'\n"
                "• Decatastrophize: 'Even if that happens, I can handle it by ___'\n"
                "• Probability scale: Rate 1-10 how likely the catastrophe is (usually <3)\n"
                "• Focus on what you CAN control, accept what you can't"
            )
        
        if 'should_statements' in distortions:
            recs.append(
                "\nShould Statements:\n"
                "You're putting pressure on yourself with 'shoulds'. Replace them:\n"
                "• 'I should' → 'I prefer' or 'I choose to' or 'It would be nice if'\n"
                "• Ask: 'Where did this rule come from? Is it really my rule?'\n"
                "• Self-compassion: 'I'm doing my best with what I have right now'\n"
                "• Realistic expectations: Perfect doesn't exist - good enough IS good enough\n"
                "• Example: Change 'I should be happy' to 'I prefer to feel happy, and I'm working toward that'"
            )
        
        if 'mind_reading' in distortions:
            recs.append(
                "\nMind Reading:\n"
                "You assume you know what others think. Reality check:\n"
                "• Ask directly: 'What did you mean by that?' - Don't assume\n"
                "• Evidence: 'What proof do I have they think this?' (Usually zero)\n"
                "• Alternative explanations: List 3 other reasons for their behavior\n"
                "• Remember: Most people are thinking about themselves, not judging you\n"
                "• Your thoughts about what they think aren't facts"
            )
        
        if 'fortune_telling' in distortions:
            recs.append(
                "\nFortune Telling:\n"
                "You predict negative futures. Ground yourself:\n"
                "• Fact vs. prediction: 'I don't know the future - this is just a prediction'\n"
                "• Past evidence: 'How many times was I wrong about predicting failure?'\n"
                "• Possibility thinking: 'It COULD go badly, but it could also go well'\n"
                "• Control what you can NOW: Focus on present actions, not future what-ifs\n"
                "• Anxiety lies: Your brain overestimates danger to protect you - it's not accurate"
            )
        
        if 'labeling' in distortions:
            recs.append(
                "\nLabeling:\n"
                "You attach harsh labels to yourself/others. Reframe:\n"
                "• Separate behavior from identity: 'I made a mistake' not 'I AM a mistake'\n"
                "• Specificity: Instead of 'I'm stupid', say 'I struggled with this specific task'\n"
                "• Counter-labels: For every negative label, list 3 positive qualities\n"
                "• Compassion: Would you call a friend that label? Then don't use it on yourself\n"
                "• Remember: You are not your actions - you're a complex human having experiences"
            )
        
        if 'personalization' in distortions:
            recs.append(
                "\nPersonalization:\n"
                "You blame yourself for things outside your control. Consider:\n"
                "• Responsibility pie: List ALL factors that contributed (you're probably <20%)\n"
                "• Ask: 'What was truly in my control?' - Only own your part\n"
                "• External factors: Other people's moods, choices, reactions aren't about you\n"
                "• Self-compassion: Everyone makes mistakes - it doesn't mean you're defective\n"
                "• Shared responsibility: Most outcomes have multiple contributors"
            )
        
        if 'overgeneralization' in distortions:
            recs.append(
                "\nOvergeneralization:\n"
                "One event becomes 'always' or 'everyone'. Be specific:\n"
                "• Quantify: 'This happened once' not 'this always happens'\n"
                "• Specific language: 'This person' not 'everyone', 'Today' not 'always'\n"
                "• Counter-examples: List times when the opposite was true\n"
                "• Sample size: One or two events don't equal a pattern\n"
                "• Stay present: This moment isn't every moment"
            )
        
        return '\n'.join(recs)
    
    def _generate_coping_reinforcement(self, coping, themes):
        """Reinforce and expand on coping strategies user is already using"""
        if not coping:
            return None
        
        recs = ["\n\n✅ Building on What's Working for You:"]
        
        strategies = []
        if 'meditation' in coping or 'breathing' in coping:
            strategies.append(
                "• Meditation/Breathing - You're already doing this! Level up:\n"
                "  - Try guided meditations on YouTube (search '10 minute anxiety meditation')\n"
                "  - Experiment with body scan meditation before bed\n"
                "  - Use apps: Insight Timer (free), Headspace, Calm"
            )
        
        if 'exercise' in coping or 'walk' in coping:
            strategies.append(
                "• Physical Activity - Great job staying active! Expand this:\n"
                "  - Vary intensity: Mix calming walks with energizing workouts\n"
                "  - Outdoor exercise: Nature exposure boosts mood 30% more than indoor\n"
                "  - Social exercise: Join a class or exercise with a friend"
            )
        
        if 'journal' in coping:
            strategies.append(
                "• Journaling - Powerful tool! Try these formats:\n"
                "  - Gratitude journal: 3 good things daily\n"
                "  - Thought records: Situation → Thought → Feeling → Alternative thought\n"
                "  - Prompt journal: 'Today I felt ___ because ___ and I coped by ___'"
            )
        
        if 'therapy' in coping or 'counseling' in coping:
            strategies.append(
                "• Therapy - Excellent! Maximize your sessions:\n"
                "  - Prepare beforehand: Write topics you want to discuss\n"
                "  - Practice between sessions: Do the homework your therapist assigns\n"
                "  - Track progress: Notice patterns across sessions"
            )
        
        if 'talk' in coping or 'friends' in coping or 'support' in coping:
            strategies.append(
                "• Social Support - Keep connecting! Deepen these connections:\n"
                "  - Be vulnerable: Share how you really feel, not just surface level\n"
                "  - Ask for specific help: 'Can you check in on me tomorrow?'\n"
                "  - Give back: Supporting others also helps you feel better"
            )
        
        if strategies:
            recs.extend(strategies)
            recs.append(
                "\nContinue what's working - Consistency matters more than perfection. "
                "Even on hard days, doing one coping strategy is progress."
            )
            return '\n'.join(recs)
        
        return None
    
    def _generate_trend_recommendations(self, trend, score, themes):
        """Generate action plan based on mood trend"""
        if trend == 'declining':
            return (
                "\n\n📉 Your Mood is Declining - Action Plan:\n"
                "Early intervention prevents crisis. Do these NOW:\n"
                "• Identify what changed: New stressor? Stopped a helpful habit? Sleep issues?\n"
                "• Increase self-care intensity: Double your coping activities this week\n"
                "• Reach out: Tell someone you trust that you're struggling\n"
                "• Schedule check-in: See your therapist sooner or book MindLift consultation\n"
                "• Prevention: Don't wait until you feel worse - act now\n"
                "• Remember: Asking for help is strength, not weakness"
            )
        elif trend == 'improving':
            return (
                "\n\n📈 Your Mood is Improving - Sustain This:\n"
                "Build momentum while you have it:\n"
                "• Document what's helping: Write down what you've been doing differently\n"
                "• Create a 'wellness formula': List specific actions that boost your mood\n"
                "• Set new goals: Use this energy to tackle something you've been avoiding\n"
                "• Plan for future dips: 'When I feel down again, I will ___'\n"
                "• Share your success: Tell someone about your progress\n"
                "• Keep going: Healing continues even when you feel better"
            )
        elif trend == 'stable':
            primary_theme = list(themes.keys())[0] if themes else None
            if primary_theme:
                return (
                    f"\n\n⚖️ Maintaining Stability While Working on {primary_theme.replace('_', ' ').title()}:\n"
                    "Consistency is key:\n"
                    "• Stick to routines: What you're doing is working - don't stop\n"
                    "• Gradual improvement: Small steps forward compound over time\n"
                    "• Challenge yourself: Take one small risk outside comfort zone weekly\n"
                    "• Anticipate obstacles: Plan how you'll handle difficult situations\n"
                    "• Celebrate stability: Staying level IS progress"
                )
        
        return None
    
    def _generate_combination_strategies(self, themes, emotions, distortions):
        """Address specific combinations of issues that often co-occur"""
        theme_list = list(themes.keys()) if themes else []
        combos = []
        
        # Anxiety + Sleep
        if 'anxiety' in theme_list and 'sleep' in theme_list:
            combos.append(
                "\n\n💤 Anxiety + Sleep Issues:\n"
                "These feed each other - break the cycle:\n"
                "• Worry postponement: If anxious at night, write worries down, promise to address at 3pm tomorrow\n"
                "• Sleep anxiety: Accept that some sleep loss is okay - anxiety about sleep makes it worse\n"
                "• Wind-down: Start relaxation 90 minutes before bed, not when you're already in bed anxious\n"
                "• Morning routine: Even if you slept poorly, get up at same time - this fixes your circadian rhythm"
            )
        
        # Depression + Work Stress
        if 'depression' in theme_list and 'work_stress' in theme_list:
            combos.append(
                "\n\n💼 Depression + Work Stress:\n"
                "Work drains energy you don't have - protect yourself:\n"
                "• Energy management: Do hardest tasks when energy is highest (usually morning)\n"
                "• Lower bar: 'Good enough' is your standard now, not 'perfect'\n"
                "• Breaks mandatory: 5 min break every hour - non-negotiable\n"
                "• Consider accommodations: Talk to HR about flexible hours or reduced workload temporarily\n"
                "• Separate identity: You are not your job - your worth isn't your productivity"
            )
        
        # Anxiety + Depression
        if 'anxiety' in theme_list and 'depression' in theme_list:
            combos.append(
                "\n\n🔄 Anxiety + Depression:\n"
                "This combo is tough but treatable:\n"
                "• Opposite action: Anxiety says 'run away', Depression says 'stay in bed' - do opposite\n"
                "• Scheduled activity: Put ONE positive activity in calendar daily (accountability helps both)\n"
                "• Focus on now: Depression focuses on past, anxiety on future - ground yourself in present\n"
                "• Medication consideration: This combo often responds well to medication + therapy\n"
                "• One thing: Just commit to one coping strategy daily - both disorders lie about ability"
            )
        
        # Relationships + Self-Esteem
        if 'relationships' in theme_list and 'self_esteem' in theme_list:
            combos.append(
                "\n\n❤️ Relationships + Self-Esteem:\n"
                "Low self-esteem affects relationships - work on both:\n"
                "• Boundaries: Saying no strengthens relationships AND self-respect\n"
                "• Stop people-pleasing: Authentic connection requires showing real you\n"
                "• Receive compliments: Say 'thank you' without deflecting - practice believing them\n"
                "• Separate worth from relationships: Being single/in conflict doesn't mean you're unworthy\n"
                "• Choose supportive people: Surround yourself with those who lift you up"
            )
        
        # Any distortion + Depression
        if distortions and 'depression' in theme_list:
            combos.append(
                "\n\n🧠 Negative Thinking + Depression:\n"
                "Depression amplifies distorted thoughts:\n"
                "• Depression filter: Everything looks worse when depressed - your thoughts aren't facts\n"
                "• Behavioral activation first: Sometimes you can't think your way out - act first, mood follows\n"
                "• Thought logs: Write thoughts down - they're less powerful on paper than in your head\n"
                "• Challenge gently: Don't fight thoughts aggressively - curiosity works better than combat\n"
                "• Get help: CBT therapy specifically targets thought patterns + depression together"
            )
        
        if combos:
            return '\n'.join(combos)
        
        return None
    
    def get_user_sentiment_trend(self, user, days=30):
        """Get detailed sentiment trend over time"""
        messages = Message.objects.filter(
            conversation__user=user,
            sender='user',
            conversation__is_deleted=False,
            timestamp__gte=datetime.now() - timedelta(days=days)
        ).order_by('timestamp')
        
        # Group by day
        daily_sentiments = {}
        for msg in messages:
            day = msg.timestamp.date()
            if day not in daily_sentiments:
                daily_sentiments[day] = []
            score = msg.sentiment_score if msg.sentiment_score is not None else 0.0
            daily_sentiments[day].append(score)
        
        # Calculate daily averages and additional metrics
        trend = []
        for day, scores in sorted(daily_sentiments.items()):
            # Calculate average manually
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            # Count sentiment types for the day
            positive_count = sum(1 for s in scores if s >= 0.05)
            negative_count = sum(1 for s in scores if s <= -0.05)
            neutral_count = len(scores) - positive_count - negative_count
            
            trend.append({
                'date': day.strftime('%Y-%m-%d'),
                'score': round(avg_score, 3),
                'label': self.analyzer.get_sentiment_label_from_score(avg_score),
                'message_count': len(scores),
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count
            })
        
        return trend