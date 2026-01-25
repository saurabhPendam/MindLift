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
        
        # Detect trends
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
            referral_count=professional_referral_needed
        )
        
        # Generate personalized recommendations
        recommendations = self._generate_recommendations(
            overall, final_avg_score, top_emotions, sentiment_trend
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
        """Calculate if sentiment is improving, declining, or stable"""
        if messages.count() < 3:
            return 'stable'
        
        # Split messages into first half and second half
        mid_point = messages.count() // 2
        first_half = messages[:mid_point]
        second_half = messages[mid_point:]
        
        # Calculate averages for each half
        first_scores = list(first_half.values_list('sentiment_score', flat=True))
        second_scores = list(second_half.values_list('sentiment_score', flat=True))
        
        first_avg = sum(first_scores) / len(first_scores) if first_scores else 0
        second_avg = sum(second_scores) / len(second_scores) if second_scores else 0
        
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
                                   crisis_count, referral_count) -> str:
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
        
        return "".join(summary_parts)
    
    def _generate_recommendations(self, sentiment: str, score: float, 
                                 emotions: Dict, trend: str) -> str:
        """Generate personalized, actionable recommendations"""
        recommendations = []
        
        # Based on overall sentiment
        if sentiment == 'negative' or score < -0.3:
            recommendations.append(
                "🔴 Priority Recommendations:\n"
                "• Consider scheduling a consultation with a mental health professional "
                "through our Doctor Consultation feature\n"
                "• Practice daily self-care: Try our guided breathing exercises (5-10 minutes)\n"
                "• Engage with supportive activities: Visit our Activities page for mood-boosting exercises\n"
                "• Connect with others: Reach out to trusted friends or family members"
            )
            
            if 'fear' in emotions or 'anxiety' in emotions:
                recommendations.append(
                    "\n\nFor Anxiety Management:\n"
                    "• Try the 4-7-8 breathing technique (breathe in for 4, hold for 7, out for 8)\n"
                    "• Practice progressive muscle relaxation\n"
                    "• Limit caffeine intake\n"
                    "• Establish a consistent sleep schedule"
                )
            
            if 'sadness' in emotions:
                recommendations.append(
                    "\n\nFor Managing Sadness:\n"
                    "• Start a gratitude journal - write 3 things you're grateful for daily\n"
                    "• Engage in physical activity - even a 10-minute walk can help\n"
                    "• Listen to uplifting music or content\n"
                    "• Allow yourself to feel emotions without judgment"
                )
        
        elif sentiment == 'neutral':
            recommendations.append(
                "🟡 Maintenance & Growth:\n"
                "• Continue your current coping strategies - they're working\n"
                "• Explore new wellness activities to prevent stagnation\n"
                "• Set small, achievable goals for personal growth\n"
                "• Maintain social connections and support networks"
            )
            
            if trend == 'declining':
                recommendations.append(
                    "\n\n⚠️ Preventive Action:\n"
                    "• Monitor your emotional state more closely\n"
                    "• Increase engagement with wellness activities\n"
                    "• Consider talking to someone about recent stressors"
                )
        
        else:  # positive
            recommendations.append(
                "🟢 Excellent Progress!\n"
                "• Keep up your current wellness practices\n"
                "• Document what's working well for you\n"
                "• Consider sharing your strategies with others who might benefit\n"
                "• Continue building on your positive momentum"
            )
            
            if 'joy' in emotions:
                recommendations.append(
                    "\n\nCelebrate Your Success:\n"
                    "• Take time to acknowledge your emotional growth\n"
                    "• Reflect on what contributed to your positive state\n"
                    "• Share your happiness with loved ones"
                )
        
        # Trend-based recommendations
        if trend == 'declining':
            recommendations.append(
                "\n\n📉 Addressing the Decline:\n"
                "• Identify recent changes or stressors in your life\n"
                "• Increase self-care activities\n"
                "• Don't hesitate to seek professional support\n"
                "• Review and adjust your current coping strategies"
            )
        elif trend == 'improving':
            recommendations.append(
                "\n\n📈 Building on Improvement:\n"
                "• Identify what's been helping and do more of it\n"
                "• Set new wellness goals\n"
                "• Consider mentoring others or sharing your journey"
            )
        
        # Emotion-specific recommendations
        if 'anger' in emotions:
            recommendations.append(
                "\n\nManaging Anger:\n"
                "• Try physical activities to release tension (walking, exercise)\n"
                "• Practice the 'pause and breathe' technique before responding\n"
                "• Journal about what's triggering your anger\n"
                "• Consider anger management resources or counseling"
            )
        
        # Always include crisis resources
        recommendations.append(
            "\n\n🆘 Immediate Support Available:\n"
            "• National Suicide Prevention Lifeline: 988\n"
            "• Crisis Text Line: Text HOME to 741741\n"
            "• Emergency: 911\n"
            "• These services are available 24/7 with trained professionals"
        )
        
        return '\n'.join(recommendations)
    
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