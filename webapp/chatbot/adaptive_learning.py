"""
Adaptive Learning System for MindLift
Continuously improves models from user interactions, feedback, and clinical outcomes
File: chatbot/adaptive_learning.py
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from chatbot.models import Message, Feedback, PHQ9Assessment, GAD7Assessment, User
import logging

logger = logging.getLogger(__name__)


class AdaptiveLearningSystem:
    """
    Self-learning system that improves from user data
    
    Features:
    1. Sentiment classifier that learns from feedback
    2. Theme extraction that adapts to user language
    3. Cognitive distortion detector trained on patterns
    4. Crisis detection calibration
    5. Coping strategy recognition from conversations
    """
    
    def __init__(self):
        self.model_dir = 'ml_models'
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize models
        self.sentiment_model = None
        self.theme_model = None
        self.distortion_model = None
        self.crisis_model = None
        
        # Load existing models if available
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models from disk"""
        try:
            sentiment_path = os.path.join(self.model_dir, 'sentiment_classifier.pkl')
            if os.path.exists(sentiment_path):
                self.sentiment_model = joblib.load(sentiment_path)
                logger.info("✅ Loaded sentiment classifier")
            
            theme_path = os.path.join(self.model_dir, 'theme_extractor.pkl')
            if os.path.exists(theme_path):
                self.theme_model = joblib.load(theme_path)
                logger.info("✅ Loaded theme extractor")
            
            distortion_path = os.path.join(self.model_dir, 'distortion_detector.pkl')
            if os.path.exists(distortion_path):
                self.distortion_model = joblib.load(distortion_path)
                logger.info("✅ Loaded distortion detector")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def save_models(self):
        """Save trained models to disk"""
        try:
            if self.sentiment_model:
                joblib.dump(self.sentiment_model, 
                          os.path.join(self.model_dir, 'sentiment_classifier.pkl'))
            
            if self.theme_model:
                joblib.dump(self.theme_model,
                          os.path.join(self.model_dir, 'theme_extractor.pkl'))
            
            if self.distortion_model:
                joblib.dump(self.distortion_model,
                          os.path.join(self.model_dir, 'distortion_detector.pkl'))
            
            logger.info("✅ Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def collect_training_data(self, days=90):
        """
        Collect training data from user interactions
        
        Training sources:
        1. Messages with sentiment scores (VADER baseline)
        2. Feedback ratings (user corrections)
        3. Clinical assessment outcomes (PHQ-9, GAD-7)
        4. Semantic analysis results (themes, distortions)
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # Get messages with sentiment analysis
        messages = Message.objects.filter(
            sender='user',
            timestamp__gte=start_date,
            sentiment_score__isnull=False
        ).select_related('conversation__user')
        
        training_data = []
        
        for msg in messages:
            # Basic features
            features = {
                'text': msg.content,
                'sentiment_score': msg.sentiment_score,
                'sentiment_label': msg.sentiment_label,
                'emotions': msg.emotions,
                'themes': msg.themes,
                'cognitive_distortions': msg.cognitive_distortions,
                'crisis_level': msg.crisis_level,
                'timestamp': msg.timestamp
            }
            
            # Check for user feedback on this conversation
            feedback = Feedback.objects.filter(
                user=msg.conversation.user,
                timestamp__gte=msg.timestamp,
                timestamp__lte=msg.timestamp + timedelta(hours=24)
            ).first()
            
            if feedback:
                features['user_rating'] = feedback.rating
                features['feedback_text'] = feedback.comment
            
            # Get clinical outcomes
            user = msg.conversation.user
            
            # PHQ-9 (depression) near this timeframe
            phq9 = PHQ9Assessment.objects.filter(
                user=user,
                timestamp__gte=msg.timestamp - timedelta(days=7),
                timestamp__lte=msg.timestamp + timedelta(days=7)
            ).first()
            
            if phq9:
                features['depression_score'] = phq9.total_score
                features['depression_severity'] = phq9.severity
            
            # GAD-7 (anxiety) near this timeframe
            gad7 = GAD7Assessment.objects.filter(
                user=user,
                timestamp__gte=msg.timestamp - timedelta(days=7),
                timestamp__lte=msg.timestamp + timedelta(days=7)
            ).first()
            
            if gad7:
                features['anxiety_score'] = gad7.total_score
                features['anxiety_severity'] = gad7.severity
            
            training_data.append(features)
        
        logger.info(f"📊 Collected {len(training_data)} training samples")
        return training_data
    
    def train_sentiment_classifier(self, training_data):
        """
        Train improved sentiment classifier
        
        Uses:
        - VADER scores as baseline labels
        - User feedback for corrections
        - Clinical scores for validation
        """
        if len(training_data) < 50:
            logger.warning("Insufficient data for training (need 50+)")
            return False
        
        # Prepare features
        texts = [d['text'] for d in training_data]
        
        # Create labels from sentiment scores
        # Corrected by user feedback if available
        labels = []
        for d in training_data:
            if 'user_rating' in d:
                # Use user feedback (1-5 scale -> negative/neutral/positive)
                if d['user_rating'] <= 2:
                    labels.append('negative')
                elif d['user_rating'] >= 4:
                    labels.append('positive')
                else:
                    labels.append('neutral')
            else:
                # Use VADER sentiment
                labels.append(d['sentiment_label'])
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        X = vectorizer.fit_transform(texts)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Logistic Regression classifier
        classifier = LogisticRegression(max_iter=1000, class_weight='balanced')
        classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"🎯 Sentiment Classifier Accuracy: {accuracy:.2%}")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        # Save model and vectorizer
        self.sentiment_model = {
            'classifier': classifier,
            'vectorizer': vectorizer,
            'accuracy': accuracy,
            'trained_date': datetime.now()
        }
        
        return True
    
    def train_theme_classifier(self, training_data):
        """
        Train theme extraction model
        
        Learns from:
        - Semantic analyzer's theme detection
        - Clinical assessment scores
        - User's primary concerns over time
        """
        if len(training_data) < 30:
            logger.warning("Insufficient data for theme training (need 30+)")
            return False
        
        # Prepare multi-label training data
        texts = [d['text'] for d in training_data]
        
        # Extract theme labels from existing semantic analysis
        theme_labels = []
        for d in training_data:
            themes = d.get('themes', {})
            # Get top theme if exists
            if themes:
                top_theme = max(themes.items(), key=lambda x: x[1])[0]
                theme_labels.append(top_theme)
            else:
                theme_labels.append('general')
        
        # Create vectorizer
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        X = vectorizer.fit_transform(texts)
        y = np.array(theme_labels)
        
        # Train classifier
        classifier = MultinomialNB()
        classifier.fit(X, y)
        
        logger.info(f"🎯 Theme Classifier trained on {len(texts)} samples")
        
        self.theme_model = {
            'classifier': classifier,
            'vectorizer': vectorizer,
            'trained_date': datetime.now()
        }
        
        return True
    
    def train_distortion_detector(self, training_data):
        """
        Train cognitive distortion detector
        
        Learns patterns from:
        - Existing regex-based detections
        - User feedback on accuracy
        - Correlation with depression/anxiety scores
        """
        # Filter messages with detected distortions
        distortion_data = [d for d in training_data if d.get('cognitive_distortions')]
        
        if len(distortion_data) < 20:
            logger.warning("Insufficient distortion data (need 20+)")
            return False
        
        texts = []
        labels = []
        
        for d in distortion_data:
            text = d['text']
            for distortion_type in d['cognitive_distortions'].keys():
                texts.append(text)
                labels.append(distortion_type)
        
        # Vectorize
        vectorizer = TfidfVectorizer(
            max_features=300,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        X = vectorizer.fit_transform(texts)
        y = np.array(labels)
        
        # Train
        classifier = MultinomialNB()
        classifier.fit(X, y)
        
        logger.info(f"🎯 Distortion Detector trained on {len(texts)} samples")
        
        self.distortion_model = {
            'classifier': classifier,
            'vectorizer': vectorizer,
            'trained_date': datetime.now()
        }
        
        return True
    
    def retrain_all_models(self, days=90):
        """
        Retrain all models with latest data
        """
        logger.info("🔄 Starting adaptive learning retraining...")
        
        # Collect training data
        training_data = self.collect_training_data(days=days)
        
        if not training_data:
            logger.warning("No training data available")
            return False
        
        # Train each model
        results = {}
        
        results['sentiment'] = self.train_sentiment_classifier(training_data)
        results['theme'] = self.train_theme_classifier(training_data)
        results['distortion'] = self.train_distortion_detector(training_data)
        
        # Save models
        self.save_models()
        
        logger.info(f"✅ Retraining complete: {results}")
        return results
    
    def predict_sentiment(self, text):
        """Predict sentiment using trained model"""
        if not self.sentiment_model:
            return None
        
        try:
            vectorizer = self.sentiment_model['vectorizer']
            classifier = self.sentiment_model['classifier']
            
            X = vectorizer.transform([text])
            prediction = classifier.predict(X)[0]
            proba = classifier.predict_proba(X)[0]
            
            return {
                'label': prediction,
                'confidence': max(proba),
                'probabilities': dict(zip(classifier.classes_, proba))
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return None
    
    def predict_themes(self, text):
        """Predict themes using trained model"""
        if not self.theme_model:
            return None
        
        try:
            vectorizer = self.theme_model['vectorizer']
            classifier = self.theme_model['classifier']
            
            X = vectorizer.transform([text])
            prediction = classifier.predict(X)[0]
            proba = classifier.predict_proba(X)[0]
            
            return {
                'theme': prediction,
                'confidence': max(proba)
            }
        except Exception as e:
            logger.error(f"Theme prediction error: {e}")
            return None
    
    def get_training_stats(self):
        """Get statistics about training data"""
        stats = {
            'total_messages': Message.objects.filter(sender='user').count(),
            'analyzed_messages': Message.objects.filter(
                sender='user',
                sentiment_score__isnull=False
            ).count(),
            'messages_with_feedback': Feedback.objects.count(),
            'users_with_phq9': PHQ9Assessment.objects.values('user').distinct().count(),
            'users_with_gad7': GAD7Assessment.objects.values('user').distinct().count(),
        }
        
        if self.sentiment_model:
            stats['sentiment_model'] = {
                'accuracy': self.sentiment_model.get('accuracy', 0),
                'trained_date': self.sentiment_model.get('trained_date')
            }
        
        return stats


# Global instance
adaptive_learning = AdaptiveLearningSystem()
