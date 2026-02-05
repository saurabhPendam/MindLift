"""
Enhanced Semantic Analyzer for Mental Health Chatbot
Provides deeper linguistic and semantic analysis beyond basic sentiment

Features:
- Semantic similarity detection
- Topic modeling and theme extraction
- Cognitive distortion detection
- Emotional pattern recognition
- Intent classification
- Linguistic style analysis
"""

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """
    Advanced semantic analysis for mental health conversations
    Complements VADER sentiment with deeper linguistic insights
    """
    
    def __init__(self):
        # Download required NLTK data (run once)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
        
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet', quiet=True)
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger', quiet=True)
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Mental health related themes
        self.mental_health_themes = {
            'anxiety': ['anxious', 'worried', 'nervous', 'panic', 'stress', 'overwhelmed', 'tension', 'fear'],
            'depression': ['sad', 'depressed', 'hopeless', 'empty', 'lonely', 'worthless', 'tired', 'exhausted'],
            'anger': ['angry', 'frustrated', 'irritated', 'mad', 'furious', 'annoyed', 'rage'],
            'sleep': ['insomnia', 'sleep', 'tired', 'exhausted', 'rest', 'awake', 'night'],
            'relationships': ['family', 'friend', 'partner', 'relationship', 'lonely', 'isolated', 'alone'],
            'work_stress': ['work', 'job', 'career', 'boss', 'deadline', 'pressure', 'performance'],
            'self_esteem': ['confidence', 'self-esteem', 'worth', 'worthless', 'failure', 'inadequate'],
            'trauma': ['trauma', 'ptsd', 'flashback', 'nightmare', 'abuse', 'violence'],
            'substance': ['alcohol', 'drugs', 'drinking', 'smoking', 'addiction'],
            'physical_health': ['pain', 'headache', 'sick', 'illness', 'health', 'body']
        }
        
        # Cognitive distortions (CBT patterns)
        self.cognitive_distortions = {
            'all_or_nothing': [
                r'\b(always|never|every|all|nothing|nobody|everyone)\b',
                r'\b(complete|total|absolute) (failure|disaster)\b'
            ],
            'overgeneralization': [
                r'\b(always|never) (happens|ends|goes)\b',
                r'\beverything (is|goes|turns)\b'
            ],
            'catastrophizing': [
                r'\b(worst|terrible|awful|disaster|horrible|catastrophe)\b',
                r'\bthe end of\b',
                r'\bcan\'t handle\b'
            ],
            'mind_reading': [
                r'\b(they think|he thinks|she thinks|people think)\b',
                r'\b(must think|probably think|surely think)\b'
            ],
            'fortune_telling': [
                r'\b(will never|won\'t ever|will always)\b',
                r'\b(going to fail|going to be terrible)\b'
            ],
            'should_statements': [
                r'\b(should|shouldn\'t|must|have to|ought to)\b'
            ],
            'labeling': [
                r'\bi am (a |an )?(loser|failure|idiot|stupid|worthless)\b',
                r'\bhe is (a |an )?(jerk|idiot)\b'
            ],
            'personalization': [
                r'\bit\'s (all )?my fault\b',
                r'\bi am (to )?blame\b'
            ]
        }
        
        # Coping indicators (positive patterns)
        self.coping_indicators = [
            'breathe', 'breathing', 'exercise', 'meditation', 'yoga',
            'therapy', 'counseling', 'support', 'help', 'talk',
            'journal', 'walk', 'nature', 'hobby', 'friends',
            'grateful', 'thankful', 'positive', 'trying', 'working on'
        ]
        
        # Crisis urgency levels
        self.crisis_patterns = {
            'immediate': [
                'kill myself', 'end my life', 'suicide', 'want to die',
                'overdose', 'jump off', 'not worth living'
            ],
            'high': [
                'hurt myself', 'self-harm', 'cutting', 'harming',
                'no reason to live', 'better off dead'
            ],
            'moderate': [
                'can\'t go on', 'give up', 'no hope', 'hopeless',
                'pointless', 'meaningless'
            ]
        }
    
    def analyze_text(self, text: str, conversation_history: Optional[List[str]] = None) -> Dict:
        """
        Comprehensive semantic analysis of text
        
        Args:
            text: User message to analyze
            conversation_history: Previous messages for context
            
        Returns:
            dict with semantic features
        """
        result = {
            'themes': self._extract_themes(text),
            'cognitive_distortions': self._detect_distortions(text),
            'coping_indicators': self._detect_coping(text),
            'crisis_level': self._assess_crisis_urgency(text),
            'linguistic_features': self._analyze_linguistic_features(text),
            'key_phrases': self._extract_key_phrases(text),
            'semantic_similarity': None
        }
        
        # Context-aware analysis if history available
        if conversation_history:
            result['semantic_similarity'] = self._calculate_semantic_similarity(
                text, conversation_history
            )
            result['conversation_patterns'] = self._analyze_conversation_patterns(
                conversation_history
            )
        
        return result
    
    def _extract_themes(self, text: str) -> Dict[str, float]:
        """Extract mental health themes from text"""
        text_lower = text.lower()
        tokens = word_tokenize(text_lower)
        
        theme_scores = {}
        for theme, keywords in self.mental_health_themes.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                # Normalize by text length
                theme_scores[theme] = matches / len(tokens) if tokens else 0
        
        # Sort by score
        return dict(sorted(theme_scores.items(), key=lambda x: x[1], reverse=True))
    
    def _detect_distortions(self, text: str) -> Dict[str, List[str]]:
        """Detect cognitive distortions (CBT)"""
        text_lower = text.lower()
        detected = {}
        
        for distortion, patterns in self.cognitive_distortions.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text_lower)
                if found:
                    matches.extend(found)
            
            if matches:
                detected[distortion] = list(set(matches))
        
        return detected
    
    def _detect_coping(self, text: str) -> List[str]:
        """Detect coping strategies mentioned"""
        text_lower = text.lower()
        found_coping = []
        
        for indicator in self.coping_indicators:
            if indicator in text_lower:
                found_coping.append(indicator)
        
        return found_coping
    
    def _assess_crisis_urgency(self, text: str) -> Dict[str, any]:
        """Assess crisis urgency level"""
        text_lower = text.lower()
        
        urgency = {
            'level': 'none',
            'matched_patterns': [],
            'confidence': 0.0
        }
        
        # Check each level
        for level in ['immediate', 'high', 'moderate']:
            for pattern in self.crisis_patterns[level]:
                if pattern in text_lower:
                    if level == 'immediate':
                        urgency['level'] = 'critical'
                        urgency['confidence'] = 1.0
                    elif level == 'high' and urgency['level'] not in ['critical']:
                        urgency['level'] = 'high'
                        urgency['confidence'] = 0.8
                    elif level == 'moderate' and urgency['level'] not in ['critical', 'high']:
                        urgency['level'] = 'moderate'
                        urgency['confidence'] = 0.5
                    
                    urgency['matched_patterns'].append(pattern)
        
        return urgency
    
    def _analyze_linguistic_features(self, text: str) -> Dict:
        """Analyze linguistic characteristics"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        
        # POS tagging
        try:
            pos_tags = nltk.pos_tag(words)
            pos_counts = Counter(tag for word, tag in pos_tags)
        except Exception as e:
            logger.error(f"POS tagging error: {e}")
            pos_counts = Counter()
        
        # First-person pronouns (indicator of self-focus)
        first_person = sum(1 for word in words if word.lower() in ['i', 'me', 'my', 'myself', 'mine'])
        
        # Negative words
        negative_words = sum(1 for word in words if word.lower() in [
            'not', 'no', 'never', 'nothing', 'nobody', 'nowhere',
            'neither', 'none', 'without', 'lack', 'can\'t', 'won\'t'
        ])
        
        return {
            'sentence_count': len(sentences),
            'word_count': len(words),
            'avg_words_per_sentence': len(words) / len(sentences) if sentences else 0,
            'first_person_pronouns': first_person,
            'first_person_ratio': first_person / len(words) if words else 0,
            'negative_word_count': negative_words,
            'negative_word_ratio': negative_words / len(words) if words else 0,
            'pos_distribution': dict(pos_counts.most_common(5))
        }
    
    def _extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """Extract key phrases using simple noun phrase extraction"""
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and lemmatize
        meaningful_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token.isalpha() and token not in self.stop_words
        ]
        
        # Get most common meaningful words
        if meaningful_tokens:
            most_common = Counter(meaningful_tokens).most_common(top_n)
            return [word for word, count in most_common]
        
        return []
    
    def _calculate_semantic_similarity(self, current_text: str, history: List[str]) -> Dict:
        """Calculate semantic similarity with conversation history"""
        if not history:
            return {'avg_similarity': 0.0, 'max_similarity': 0.0}
        
        try:
            # Combine current and history
            all_texts = [current_text] + history[-10:]  # Last 10 messages
            
            # TF-IDF vectorization
            vectorizer = TfidfVectorizer(max_features=100)
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarity of current with each historical message
            current_vector = tfidf_matrix[0:1]
            history_vectors = tfidf_matrix[1:]
            
            similarities = cosine_similarity(current_vector, history_vectors)[0]
            
            return {
                'avg_similarity': float(np.mean(similarities)),
                'max_similarity': float(np.max(similarities)),
                'min_similarity': float(np.min(similarities)),
                'std_similarity': float(np.std(similarities))
            }
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return {'avg_similarity': 0.0, 'max_similarity': 0.0}
    
    def _analyze_conversation_patterns(self, history: List[str]) -> Dict:
        """Analyze patterns across conversation"""
        if len(history) < 2:
            return {'message_length_trend': 'insufficient_data'}
        
        # Analyze message lengths
        lengths = [len(msg.split()) for msg in history]
        
        # Detect trend
        if len(lengths) >= 3:
            early_avg = np.mean(lengths[:len(lengths)//2])
            late_avg = np.mean(lengths[len(lengths)//2:])
            
            if late_avg > early_avg * 1.2:
                trend = 'increasing'  # More verbose over time
            elif late_avg < early_avg * 0.8:
                trend = 'decreasing'  # Becoming more brief
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'message_length_trend': trend,
            'avg_message_length': float(np.mean(lengths)),
            'message_count': len(history)
        }
    
    def generate_insights(self, analysis: Dict) -> Dict[str, str]:
        """Generate human-readable insights from analysis"""
        insights = {}
        
        # Theme insights
        if analysis['themes']:
            top_theme = list(analysis['themes'].keys())[0]
            insights['primary_concern'] = f"Primary concern appears to be {top_theme.replace('_', ' ')}"
        
        # Distortion insights
        if analysis['cognitive_distortions']:
            distortions = list(analysis['cognitive_distortions'].keys())
            insights['thinking_patterns'] = f"Detected thinking patterns: {', '.join(distortions[:3])}"
        
        # Coping insights
        if analysis['coping_indicators']:
            insights['coping_strategies'] = f"Using coping strategies: {', '.join(analysis['coping_indicators'][:3])}"
        
        # Crisis insights
        if analysis['crisis_level']['level'] != 'none':
            insights['urgency'] = f"Crisis level: {analysis['crisis_level']['level']}"
        
        # Linguistic insights
        ling = analysis['linguistic_features']
        if ling['first_person_ratio'] > 0.15:
            insights['self_focus'] = "High self-focus detected (may indicate rumination)"
        
        if ling['negative_word_ratio'] > 0.1:
            insights['negative_language'] = "Significant negative language detected"
        
        return insights


# Singleton instance
semantic_analyzer = SemanticAnalyzer()
