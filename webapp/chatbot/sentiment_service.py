"""
Sentiment Analysis Service using VADER and NRCLex
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nrclex import NRCLex
import re
from typing import Dict, Tuple
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from chatbot.models import Message, SentimentReport


class SentimentAnalyzer:
    """Handles sentiment analysis using VADER and NRCLex"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of text using VADER and NRCLex
        
        Returns:
            dict: {
                'vader': {'compound': float, 'pos': float, 'neu': float, 'neg': float},
                'label': str ('positive', 'negative', 'neutral'),
                'emotions': dict (NRC emotions)
            }
        """
        # VADER Sentiment Analysis
        vader_scores = self.vader.polarity_scores(text)
        
        # Determine sentiment label
        compound = vader_scores['compound']
        if compound >= 0.05:
            label = 'positive'
        elif compound <= -0.05:
            label = 'negative'
        else:
            label = 'neutral'
        
        # NRCLex Emotion Analysis
        emotion_obj = NRCLex(text)
        emotions = emotion_obj.raw_emotion_scores
        
        # Get top emotions
        top_emotions = emotion_obj.top_emotions
        
        return {
            'vader': vader_scores,
            'label': label,
            'score': compound,
            'emotions': emotions,
            'top_emotions': top_emotions,
            'affect_frequencies': emotion_obj.affect_frequencies
        }
    
    def analyze_message(self, message_obj) -> Dict:
        """Analyze a message object and update it with sentiment data"""
        result = self.analyze_text(message_obj.content)
        
        # Update message with sentiment data
        message_obj.sentiment_score = result['score']
        message_obj.sentiment_label = result['label']
        message_obj.emotions = result['emotions']
        message_obj.save()
        
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
    """Generate sentiment analysis reports"""
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
    
    def generate_conversation_report(self, conversation, user) -> Dict:
        """Generate report for a specific conversation"""
        messages = Message.objects.filter(
            conversation=conversation,
            sender='user'
        )
        
        return self._calculate_metrics(messages, user, conversation)
    
    def generate_user_report(self, user, days=7) -> Dict:
        """Generate report for user's messages over specified days"""
        start_date = datetime.now() - timedelta(days=days)
        
        messages = Message.objects.filter(
            conversation__user=user,
            sender='user',
            timestamp__gte=start_date
        )
        
        return self._calculate_metrics(messages, user, days=days)
    
    def _calculate_metrics(self, messages, user, conversation=None, days=None) -> Dict:
        """Calculate sentiment metrics from messages"""
        if not messages.exists():
            return {
                'error': 'No messages found',
                'total_messages': 0
            }
        
        # Count sentiments
        total = messages.count()
        positive = messages.filter(sentiment_label='positive').count()
        negative = messages.filter(sentiment_label='negative').count()
        neutral = messages.filter(sentiment_label='neutral').count()
        
        # Calculate percentages
        pos_pct = (positive / total * 100) if total > 0 else 0
        neg_pct = (negative / total * 100) if total > 0 else 0
        neu_pct = (neutral / total * 100) if total > 0 else 0
        
        # Average sentiment score
        avg_score = messages.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
        
        # Determine overall sentiment
        if avg_score >= 0.05:
            overall = 'positive'
        elif avg_score <= -0.05:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        # Aggregate emotions across all messages
        all_emotions = {}
        for msg in messages:
            if msg.emotions:
                for emotion, score in msg.emotions.items():
                    all_emotions[emotion] = all_emotions.get(emotion, 0) + score
        
        # Get top 5 emotions
        sorted_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)
        top_emotions = dict(sorted_emotions[:5])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(overall, avg_score, top_emotions)
        
        # Create report object
        if days:
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now()
        else:
            start_date = messages.first().timestamp
            end_date = messages.last().timestamp
        
        report = SentimentReport.objects.create(
            user=user,
            conversation=conversation,
            start_date=start_date,
            end_date=end_date,
            overall_sentiment=overall,
            average_score=avg_score,
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
        
        return {
            'report_id': report.id,
            'overall_sentiment': overall,
            'average_score': round(avg_score, 3),
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
            'recommendations': recommendations.split('\n'),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
    
    def _generate_recommendations(self, sentiment: str, score: float, emotions: Dict) -> str:
        """Generate personalized recommendations based on sentiment analysis"""
        recommendations = []
        
        if sentiment == 'negative' or score < -0.3:
            recommendations.append("Consider reaching out to a mental health professional through our Doctor Consultation feature")
            recommendations.append("Try breathing exercises or meditation from the Activities page")
            recommendations.append("Engage with uplifting content - visit our Motivational Quotes section")
            
            if 'fear' in emotions or 'sadness' in emotions:
                recommendations.append("Practice grounding techniques to manage anxiety")
                recommendations.append("Journal your thoughts to process difficult emotions")
        
        elif sentiment == 'neutral':
            recommendations.append("Maintain your current coping strategies")
            recommendations.append("Continue regular self-care practices")
            recommendations.append("Explore new activities to boost your mood")
        
        else:  # positive
            recommendations.append("Great job maintaining positive mental health!")
            recommendations.append("Continue your current wellness practices")
            recommendations.append("Consider sharing your strategies with others")
        
        # Emotion-specific recommendations
        if 'anger' in emotions:
            recommendations.append("Practice anger management techniques")
            recommendations.append("Try physical activities to release tension")
        
        if 'joy' in emotions and emotions['joy'] > 0:
            recommendations.append("Celebrate your positive moments")
            recommendations.append("Share your happiness with others")
        
        return '\n'.join(recommendations)
    
    def get_user_sentiment_trend(self, user, days=30):
        """Get sentiment trend over time"""
        messages = Message.objects.filter(
            conversation__user=user,
            sender='user',
            timestamp__gte=datetime.now() - timedelta(days=days)
        ).order_by('timestamp')
        
        # Group by day
        daily_sentiments = {}
        for msg in messages:
            day = msg.timestamp.date()
            if day not in daily_sentiments:
                daily_sentiments[day] = []
            daily_sentiments[day].append(msg.sentiment_score or 0)
        
        # Calculate daily averages
        trend = []
        for day, scores in sorted(daily_sentiments.items()):
            avg_score = sum(scores) / len(scores)
            trend.append({
                'date': day.strftime('%Y-%m-%d'),
                'score': round(avg_score, 3),
                'label': self.analyzer.get_sentiment_label_from_score(avg_score),
                'message_count': len(scores)
            })
        
        return trend


def extract_youtube_url(text: str) -> str:
    """Extract YouTube URL from text"""
    # Patterns for YouTube URLs
    patterns = [
        r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(https?://)?(www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            video_id = match.group(4) if 'watch' in pattern or 'youtu.be' in pattern else match.group(3)
            return f"https://www.youtube.com/embed/{video_id}"
    
    return None


def get_youtube_video_id(url: str) -> str:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None