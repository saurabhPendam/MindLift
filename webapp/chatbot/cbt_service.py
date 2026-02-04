"""
CBT Service - Cognitive Behavioral Therapy Integration
Provides evidence-based CBT interventions integrated with Self-Determination Theory
"""
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count
import numpy as np
from scipy import stats


class CBTService:
    """
    Cognitive Behavioral Therapy service implementing evidence-based interventions.
    Integrates SDT (Self-Determination Theory) principles for motivation and engagement.
    """
    
    # Common cognitive distortions
    COGNITIVE_DISTORTIONS = {
        'all_or_nothing': 'All-or-Nothing Thinking',
        'overgeneralization': 'Overgeneralization',
        'mental_filter': 'Mental Filter',
        'disqualifying_positive': 'Disqualifying the Positive',
        'jumping_to_conclusions': 'Jumping to Conclusions',
        'magnification': 'Magnification (Catastrophizing)',
        'emotional_reasoning': 'Emotional Reasoning',
        'should_statements': 'Should Statements',
        'labeling': 'Labeling',
        'personalization': 'Personalization'
    }
    
    @staticmethod
    def identify_distortions(thought_text):
        """
        Identify potential cognitive distortions in a thought.
        Uses keyword matching and patterns (can be enhanced with ML).
        """
        distortions = []
        thought_lower = thought_text.lower()
        
        # All-or-nothing thinking
        if any(word in thought_lower for word in ['always', 'never', 'every', 'nothing', 'nobody']):
            distortions.append('all_or_nothing')
        
        # Overgeneralization
        if any(word in thought_lower for word in ['everyone', 'everything', 'all the time']):
            distortions.append('overgeneralization')
        
        # Catastrophizing
        if any(word in thought_lower for word in ['terrible', 'awful', 'disaster', 'worst', 'horrible']):
            distortions.append('magnification')
        
        # Should statements
        if any(word in thought_lower for word in ['should', 'must', 'ought', 'have to']):
            distortions.append('should_statements')
        
        # Emotional reasoning
        if 'feel like' in thought_lower or 'i feel' in thought_lower:
            distortions.append('emotional_reasoning')
        
        return distortions
    
    @staticmethod
    def generate_socratic_questions(distortion_type):
        """
        Generate Socratic questions to challenge cognitive distortions.
        """
        questions = {
            'all_or_nothing': [
                "Is this situation really all or nothing, or are there shades of gray?",
                "What would be a more balanced way to think about this?",
                "Can you think of any exceptions to this rule?"
            ],
            'overgeneralization': [
                "Is this true in every single case, or just sometimes?",
                "Can you think of times when this wasn't the case?",
                "What evidence do you have that contradicts this generalization?"
            ],
            'magnification': [
                "How likely is it that the worst-case scenario will actually happen?",
                "How have you coped with similar situations in the past?",
                "In 5 years, how important will this be?"
            ],
            'should_statements': [
                "Who says you 'should' do this? Where does this rule come from?",
                "What would happen if you replaced 'should' with 'could' or 'want to'?",
                "Is this expectation realistic and helpful?"
            ],
            'emotional_reasoning': [
                "Just because you feel something is true, does that make it a fact?",
                "What objective evidence supports or contradicts this feeling?",
                "How might you feel about this tomorrow or next week?"
            ]
        }
        
        return questions.get(distortion_type, [
            "What evidence supports this thought?",
            "What evidence contradicts this thought?",
            "What would you tell a friend who had this thought?"
        ])
    
    @staticmethod
    def create_behavioral_activation_plan(user, depression_severity='moderate'):
        """
        Create a personalized behavioral activation plan based on SDT principles.
        Emphasizes autonomy, competence, and relatedness.
        """
        from .models import CBTBehavioralActivation
        
        # Activity suggestions based on severity and SDT principles
        activities = {
            'mild': [
                {'name': 'Morning Walk', 'type': 'physical', 'pleasure': 7, 'mastery': 5, 'competence': True},
                {'name': 'Call a Friend', 'type': 'social', 'pleasure': 8, 'mastery': 4, 'relatedness': True},
                {'name': 'Learn Something New', 'type': 'mastery', 'pleasure': 6, 'mastery': 8, 'competence': True},
            ],
            'moderate': [
                {'name': '10-Minute Walk', 'type': 'physical', 'pleasure': 6, 'mastery': 6, 'competence': True},
                {'name': 'Shower and Dress', 'type': 'self_care', 'pleasure': 5, 'mastery': 7, 'autonomy': True},
                {'name': 'Text a Supportive Person', 'type': 'social', 'pleasure': 7, 'mastery': 5, 'relatedness': True},
            ],
            'severe': [
                {'name': 'Get Out of Bed', 'type': 'self_care', 'pleasure': 4, 'mastery': 8, 'autonomy': True},
                {'name': '5-Minute Breathing Exercise', 'type': 'self_care', 'pleasure': 5, 'mastery': 6, 'competence': True},
                {'name': 'Eat a Small Meal', 'type': 'self_care', 'pleasure': 5, 'mastery': 7, 'autonomy': True},
            ]
        }
        
        recommended_activities = activities.get(depression_severity, activities['moderate'])
        
        return {
            'activities': recommended_activities,
            'rationale': 'Behavioral activation helps break the cycle of depression by increasing engagement in rewarding activities.',
            'sdt_alignment': 'Activities are chosen to support your autonomy, build competence, and foster social connection.'
        }
    
    @staticmethod
    def create_exposure_hierarchy(fear_target, fear_level):
        """
        Create a graded exposure hierarchy for anxiety treatment.
        """
        # This would be customized based on the specific fear
        # Example template for social anxiety
        template_hierarchy = [
            {"step": "Imagine the feared situation", "suds": 20, "completed": False},
            {"step": "Write about the feared situation", "suds": 30, "completed": False},
            {"step": "Watch videos related to the situation", "suds": 40, "completed": False},
            {"step": "Practice the situation with a supportive person", "suds": 50, "completed": False},
            {"step": "Brief exposure to the real situation", "suds": 60, "completed": False},
            {"step": "Extended exposure to the real situation", "suds": 70, "completed": False},
            {"step": "Repeated exposure until anxiety decreases", "suds": 80, "completed": False},
        ]
        
        return template_hierarchy
    
    @staticmethod
    def get_cbt_prompt_integration(message, context=None):
        """
        Quick CBT technique detection for prompt enhancement.
        Returns technique suggestions if CBT-relevant patterns are detected.
        """
        message_lower = message.lower()
        
        # Detect cognitive distortion patterns
        if any(word in message_lower for word in ['always', 'never', 'everyone', 'nobody', 'worst', 'terrible']):
            return {
                'technique': 'Cognitive Restructuring',
                'prompts': [
                    'Help user identify cognitive distortions (all-or-nothing thinking, catastrophizing)',
                    'Use Socratic questioning to examine evidence',
                    'Guide toward more balanced thinking'
                ]
            }
        
        # Detect anxiety/worry patterns
        if any(word in message_lower for word in ['worried', 'anxious', 'nervous', 'scared', 'afraid', 'panic']):
            return {
                'technique': 'Anxiety Management',
                'prompts': [
                    'Explore specific anxiety triggers',
                    'Suggest grounding techniques or breathing exercises',
                    'Consider gradual exposure if appropriate'
                ]
            }
        
        # Detect depressive/avoidance patterns
        if any(word in message_lower for word in ['depressed', 'sad', "can't do", 'unmotivated', 'tired', 'hopeless']):
            return {
                'technique': 'Behavioral Activation',
                'prompts': [
                    'Explore activity withdrawal and avoidance',
                    'Suggest small, achievable behavioral experiments',
                    'Build on existing strengths and past successes'
                ]
            }
        
        # Detect rumination patterns
        if any(word in message_lower for word in ['keep thinking', 'can\'t stop', 'over and over', 'obsessing']):
            return {
                'technique': 'Rumination Interruption',
                'prompts': [
                    'Acknowledge the thought pattern without judgment',
                    'Suggest mindfulness or thought-defusion techniques',
                    'Redirect toward problem-solving if appropriate'
                ]
            }
        
        return None
    
    @staticmethod
    def generate_cbt_intervention_prompt(user_message, conversation_history, assessment_scores=None):
        """
        Generate a CBT-informed prompt for the AI chatbot.
        Integrates CBT techniques with SDT principles.
        """
        prompt = f"""
You are a mental health support chatbot trained in Cognitive Behavioral Therapy (CBT) and Self-Determination Theory (SDT).

USER MESSAGE: {user_message}

THERAPEUTIC APPROACH:
1. **CBT Principles**: Help users identify and challenge negative automatic thoughts, recognize cognitive distortions, and develop more balanced thinking patterns.

2. **Self-Determination Theory**: Support three basic psychological needs:
   - Autonomy: Emphasize user choice and self-direction
   - Competence: Build confidence through achievable goals and skill development
   - Relatedness: Foster connection and normalize experiences

3. **Evidence-Based Techniques**:
   - Socratic questioning to examine thoughts
   - Behavioral activation for depression
   - Exposure strategies for anxiety
   - Thought records for cognitive restructuring

ASSESSMENT CONTEXT:
{f"Recent PHQ-9 Score: {assessment_scores.get('phq9')} (Depression: {assessment_scores.get('phq9_severity')})" if assessment_scores and 'phq9' in assessment_scores else ""}
{f"Recent GAD-7 Score: {assessment_scores.get('gad7')} (Anxiety: {assessment_scores.get('gad7_severity')})" if assessment_scores and 'gad7' in assessment_scores else ""}

RESPONSE GUIDELINES:
- Be warm, empathetic, and non-judgmental
- Ask thoughtful questions that promote self-reflection
- Offer evidence-based CBT techniques when appropriate
- Support autonomy by offering choices rather than directives
- Validate emotions while gently challenging unhelpful thoughts
- Suggest concrete behavioral experiments or activities
- Normalize struggles and emphasize the therapeutic process

Respond to the user with therapeutic support:
"""
        return prompt


class AssessmentAnalytics:
    """
    Analytics service for PHQ-9 and GAD-7 assessments.
    Calculates effect sizes, tracks outcomes, and generates insights.
    """
    
    @staticmethod
    def calculate_cohens_d(baseline_scores, followup_scores):
        """
        Calculate Cohen's d effect size.
        d = (M1 - M2) / SD_pooled
        """
        if not baseline_scores or not followup_scores:
            return None
        
        baseline = np.array(baseline_scores)
        followup = np.array(followup_scores)
        
        n1, n2 = len(baseline), len(followup)
        mean1, mean2 = np.mean(baseline), np.mean(followup)
        std1, std2 = np.std(baseline, ddof=1), np.std(followup, ddof=1)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return None
        
        cohens_d = (mean1 - mean2) / pooled_std
        return cohens_d
    
    @staticmethod
    def interpret_effect_size(d):
        """
        Interpret Cohen's d effect size.
        """
        if d is None:
            return "Cannot calculate"
        
        abs_d = abs(d)
        if abs_d < 0.2:
            return "Negligible"
        elif abs_d < 0.5:
            return "Small"
        elif abs_d < 0.8:
            return "Medium"
        else:
            return "Large"
    
    @staticmethod
    def calculate_reliable_change_index(baseline, followup, test_sd, reliability):
        """
        Calculate Reliable Change Index (RCI) for clinical significance.
        RCI = (X2 - X1) / SE_diff
        """
        se_measurement = test_sd * np.sqrt(1 - reliability)
        se_diff = np.sqrt(2 * se_measurement**2)
        
        rci = (followup - baseline) / se_diff
        
        # RCI > 1.96 indicates statistically reliable change (p < .05)
        return rci, abs(rci) > 1.96
    
    @staticmethod
    def generate_progress_report(user):
        """
        Generate a comprehensive progress report for a user.
        """
        from .models import PHQ9Assessment, GAD7Assessment, InterventionOutcome
        
        # Get all assessments
        phq9_assessments = PHQ9Assessment.objects.filter(user=user).order_by('completed_at')
        gad7_assessments = GAD7Assessment.objects.filter(user=user).order_by('completed_at')
        
        if not phq9_assessments.exists() and not gad7_assessments.exists():
            return None
        
        report = {
            'user': user.username,
            'report_date': timezone.now().isoformat(),
            'depression_data': None,
            'anxiety_data': None,
            'overall_progress': None,
        }
        
        # Analyze PHQ-9 data
        if phq9_assessments.exists():
            phq9_scores = [a.total_score for a in phq9_assessments]
            baseline_phq9 = phq9_scores[0]
            current_phq9 = phq9_scores[-1]
            change_phq9 = baseline_phq9 - current_phq9
            percent_change = (change_phq9 / baseline_phq9 * 100) if baseline_phq9 > 0 else 0
            
            report['depression_data'] = {
                'baseline_score': baseline_phq9,
                'current_score': current_phq9,
                'change': change_phq9,
                'percent_change': round(percent_change, 1),
                'assessments_completed': len(phq9_scores),
                'clinically_significant': percent_change >= 50,
                'trend': 'improving' if change_phq9 > 0 else 'worsening' if change_phq9 < 0 else 'stable'
            }
        
        # Analyze GAD-7 data
        if gad7_assessments.exists():
            gad7_scores = [a.total_score for a in gad7_assessments]
            baseline_gad7 = gad7_scores[0]
            current_gad7 = gad7_scores[-1]
            change_gad7 = baseline_gad7 - current_gad7
            percent_change = (change_gad7 / baseline_gad7 * 100) if baseline_gad7 > 0 else 0
            
            report['anxiety_data'] = {
                'baseline_score': baseline_gad7,
                'current_score': current_gad7,
                'change': change_gad7,
                'percent_change': round(percent_change, 1),
                'assessments_completed': len(gad7_scores),
                'clinically_significant': percent_change >= 50,
                'trend': 'improving' if change_gad7 > 0 else 'worsening' if change_gad7 < 0 else 'stable'
            }
        
        # Overall assessment
        improvements = []
        if report['depression_data'] and report['depression_data']['change'] > 0:
            improvements.append('depression symptoms')
        if report['anxiety_data'] and report['anxiety_data']['change'] > 0:
            improvements.append('anxiety symptoms')
        
        report['overall_progress'] = {
            'showing_improvement': len(improvements) > 0,
            'areas_of_improvement': improvements,
            'recommendation': AssessmentAnalytics._generate_recommendation(report)
        }
        
        return report
    
    @staticmethod
    def _generate_recommendation(report):
        """Generate personalized recommendations based on progress."""
        recommendations = []
        
        if report['depression_data']:
            if report['depression_data']['trend'] == 'improving':
                recommendations.append("Continue with your current therapeutic activities. You're making great progress!")
            elif report['depression_data']['current_score'] >= 15:
                recommendations.append("Consider increasing behavioral activation activities and discussing treatment options with a mental health professional.")
        
        if report['anxiety_data']:
            if report['anxiety_data']['trend'] == 'improving':
                recommendations.append("Your anxiety management strategies are working well. Keep practicing them!")
            elif report['anxiety_data']['current_score'] >= 10:
                recommendations.append("Practice relaxation techniques daily and consider exposure exercises for specific fears.")
        
        if not recommendations:
            recommendations.append("Continue monitoring your symptoms with regular assessments.")
        
        return " ".join(recommendations)


class SDTFramework:
    """
    Self-Determination Theory integration for motivation and engagement.
    Supports autonomy, competence, and relatedness.
    """
    
    @staticmethod
    def assess_autonomy(user_choice, external_pressure):
        """
        Assess degree of autonomy in decision-making.
        High autonomy = self-chosen, low autonomy = externally pressured
        """
        return {
            'level': 'high' if user_choice and not external_pressure else 'medium' if user_choice else 'low',
            'score': 7 if user_choice and not external_pressure else 4 if user_choice else 2
        }
    
    @staticmethod
    def build_competence_feedback(success_rate, difficulty):
        """
        Generate competence-supporting feedback.
        Optimal challenge leads to flow state.
        """
        if success_rate > 0.8:
            return "You're mastering this skill! You might be ready for a bigger challenge."
        elif success_rate > 0.5:
            return "You're making steady progress. This level of challenge is helping you grow."
        else:
            return "This is challenging, but every attempt builds your skills. Let's break it down into smaller steps."
    
    @staticmethod
    def foster_relatedness(user):
        """
        Strategies to foster sense of connection and belonging.
        """
        return {
            'normalize_experiences': "Many people face similar challenges. You're not alone in this journey.",
            'therapeutic_alliance': "I'm here to support you through this process.",
            'community_connection': "Consider connecting with others who understand what you're going through."
        }
