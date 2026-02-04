from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import json
import uuid
import random
import string

class UserProfile(models.Model):
    """Extended user profile for additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    ], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Account deletion tracking
    deletion_requested = models.BooleanField(default=False)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    deletion_scheduled_for = models.DateTimeField(null=True, blank=True)
    
    # 2FA fields
    two_factor_enabled = models.BooleanField(default=True)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    is_authorized_email = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def request_deletion(self, grace_period_days=30):
        """Request account deletion with grace period"""
        self.deletion_requested = True
        self.deletion_requested_at = timezone.now()
        self.deletion_scheduled_for = timezone.now() + timedelta(days=grace_period_days)
        self.save()
    
    def cancel_deletion(self):
        """Cancel pending account deletion"""
        self.deletion_requested = False
        self.deletion_requested_at = None
        self.deletion_scheduled_for = None
        self.save()
    
    def days_active(self):
        """Calculate days since account creation"""
        delta = timezone.now() - self.created_at
        return delta.days

    class Meta:
        db_table = 'user_profiles'


class Conversation(models.Model):
    """Store conversation sessions with unique session IDs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    title = models.CharField(max_length=200, default="New Conversation")
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.session_id})"
    
    def soft_delete(self):
        """Soft delete the conversation and associated reports"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()
        
        # Also mark associated sentiment reports as deleted
        SentimentReport.objects.filter(conversation=self).update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
    
    def message_count(self):
        """Get total message count"""
        return self.messages.count()
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at']


class Message(models.Model):
    """Store individual messages"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[
        ('user', 'User'),
        ('bot', 'Bot')
    ])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Sentiment Analysis Fields
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=20, null=True, blank=True)
    
    # NRC Emotions
    emotions = models.JSONField(default=dict, blank=True)
    
    # Metadata
    has_video = models.BooleanField(default=False)
    video_url = models.URLField(null=True, blank=True)
    
    # LLM metadata
    model_used = models.CharField(max_length=50, default='groq', blank=True)
    
    # AI Safety flags
    contains_crisis_keywords = models.BooleanField(default=False)
    requires_professional_referral = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."
    
    class Meta:
        db_table = 'messages'
        ordering = ['timestamp']


class SentimentReport(models.Model):
    """Store sentiment analysis reports"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sentiment_reports')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Overall sentiment
    overall_sentiment = models.CharField(max_length=20)
    average_score = models.FloatField()
    
    # Sentiment breakdown
    positive_percentage = models.FloatField()
    negative_percentage = models.FloatField()
    neutral_percentage = models.FloatField()
    
    # Message counts
    total_messages = models.IntegerField()
    positive_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    
    # Dominant emotions (from NRC)
    dominant_emotions = models.JSONField(default=dict)
    
    # Recommendations
    recommendations = models.TextField(blank=True)
    
    # Deletion tracking
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Report {self.created_at.strftime('%Y-%m-%d')}"
    
    def soft_delete(self):
        """Soft delete the report"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = 'sentiment_reports'
        ordering = ['-created_at']


class Activity(models.Model):
    """Activities to help users when feeling low"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('breathing', 'Breathing Exercise'),
        ('meditation', 'Meditation'),
        ('physical', 'Physical Activity'),
        ('creative', 'Creative Activity'),
        ('social', 'Social Connection'),
        ('mindfulness', 'Mindfulness'),
        ('relaxation', 'Relaxation')
    ])
    duration_minutes = models.IntegerField(help_text="Estimated duration in minutes")
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    instructions = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        db_table = 'activities'
        verbose_name_plural = 'Activities'


class UserActivity(models.Model):
    """Track user activity completions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_activities')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(null=True, blank=True, choices=[
        (1, 'Not Helpful'),
        (2, 'Slightly Helpful'),
        (3, 'Moderately Helpful'),
        (4, 'Very Helpful'),
        (5, 'Extremely Helpful')
    ])
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.activity.title}"
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-completed_at']


class MotivationalQuote(models.Model):
    """Store motivational quotes"""
    quote = models.TextField()
    author = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=[
        ('motivation', 'Motivation'),
        ('inspiration', 'Inspiration'),
        ('hope', 'Hope'),
        ('strength', 'Strength'),
        ('peace', 'Peace'),
        ('happiness', 'Happiness'),
        ('resilience', 'Resilience')
    ])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quote[:50]}... - {self.author}"
    
    class Meta:
        db_table = 'motivational_quotes'


class UserQuoteFavorite(models.Model):
    """Track user's favorite quotes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_quotes')
    quote = models.ForeignKey(MotivationalQuote, on_delete=models.CASCADE)
    favorited_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.quote.quote[:30]}..."
    
    class Meta:
        db_table = 'user_quote_favorites'
        unique_together = ['user', 'quote']


class DoctorAppointment(models.Model):
    """Store doctor appointment bookings"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor_name = models.CharField(max_length=100)
    appointment_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=30)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('missed', 'Missed')
    ], default='scheduled')
    notes = models.TextField(blank=True)
    meeting_link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Dr. {self.doctor_name} - {self.appointment_date}"
    
    class Meta:
        db_table = 'doctor_appointments'
        ordering = ['-appointment_date']


class AuditLog(models.Model):
    """Track important user actions for security and compliance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    action = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Security categorization
    category = models.CharField(max_length=50, choices=[
        ('account', 'Account Management'),
        ('data', 'Data Access'),
        ('security', 'Security Event'),
        ('crisis', 'Crisis Detection'),
        ('deletion', 'Data Deletion')
    ], default='account')
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} - {self.action} - {self.timestamp}"
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']


class OTPVerification(models.Model):
    """Store OTP codes for 2FA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    
    def is_valid(self):
        """Check if OTP is still valid"""
        if self.is_used or self.is_verified:
            return False
        if timezone.now() > self.expires_at:
            return False
        if self.attempt_count >= 5:  # Max 5 attempts
            return False
        return True
    
    def verify(self, input_otp):
        """Verify the OTP code"""
        self.attempt_count += 1
        self.save()
        
        if not self.is_valid():
            return False
        
        if self.otp_code == input_otp:
            self.is_verified = True
            self.is_used = True
            self.save()
            return True
        return False
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def __str__(self):
        return f"{self.user.username} - OTP - {'Valid' if self.is_valid() else 'Expired'}"
    
    class Meta:
        db_table = 'otp_verifications'
        ordering = ['-created_at']


class AuthorizedEmail(models.Model):
    """Store authorized Gmail accounts"""
    email = models.EmailField(unique=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_authorized_emails')
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.email} - {'Active' if self.is_active else 'Inactive'}"
    
    @staticmethod
    def is_authorized(email):
        """Check if an email is authorized"""
        if not email:
            return False
        email = email.lower().strip()
        # Check if it's a Gmail account
        if not email.endswith('@gmail.com'):
            return False
        # Check if it's in the authorized list
        return AuthorizedEmail.objects.filter(email=email, is_active=True).exists()
    
    class Meta:
        db_table = 'authorized_emails'
        ordering = ['-added_at']


class PHQ9Assessment(models.Model):
    """
    Patient Health Questionnaire-9 (PHQ-9) for depression screening.
    Validated clinical scale for measuring depression severity.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phq9_assessments')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assessment type
    assessment_type = models.CharField(max_length=20, choices=[
        ('baseline', 'Baseline'),
        ('follow_up', 'Follow-up'),
        ('weekly', 'Weekly Check-in'),
        ('crisis', 'Crisis Assessment')
    ], default='baseline')
    
    # PHQ-9 Questions (0-3 scale: Not at all, Several days, More than half the days, Nearly every day)
    q1_interest = models.IntegerField(help_text="Little interest or pleasure in doing things")
    q2_depressed = models.IntegerField(help_text="Feeling down, depressed, or hopeless")
    q3_sleep = models.IntegerField(help_text="Trouble falling/staying asleep, or sleeping too much")
    q4_fatigue = models.IntegerField(help_text="Feeling tired or having little energy")
    q5_appetite = models.IntegerField(help_text="Poor appetite or overeating")
    q6_failure = models.IntegerField(help_text="Feeling bad about yourself or that you are a failure")
    q7_concentration = models.IntegerField(help_text="Trouble concentrating on things")
    q8_psychomotor = models.IntegerField(help_text="Moving or speaking slowly or being fidgety/restless")
    q9_suicidal = models.IntegerField(help_text="Thoughts of being better off dead or hurting yourself")
    
    # Calculated fields
    total_score = models.IntegerField(help_text="Sum of all items (0-27)")
    severity = models.CharField(max_length=20, choices=[
        ('minimal', 'Minimal (0-4)'),
        ('mild', 'Mild (5-9)'),
        ('moderate', 'Moderate (10-14)'),
        ('moderately_severe', 'Moderately Severe (15-19)'),
        ('severe', 'Severe (20-27)')
    ])
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    clinical_notes = models.TextField(blank=True)
    requires_intervention = models.BooleanField(default=False)
    
    def calculate_score(self):
        """Calculate total PHQ-9 score and determine severity"""
        self.total_score = (
            self.q1_interest + self.q2_depressed + self.q3_sleep + 
            self.q4_fatigue + self.q5_appetite + self.q6_failure + 
            self.q7_concentration + self.q8_psychomotor + self.q9_suicidal
        )
        
        # Determine severity
        if self.total_score <= 4:
            self.severity = 'minimal'
        elif self.total_score <= 9:
            self.severity = 'mild'
        elif self.total_score <= 14:
            self.severity = 'moderate'
        elif self.total_score <= 19:
            self.severity = 'moderately_severe'
        else:
            self.severity = 'severe'
        
        # Flag for intervention if moderate or higher, or suicidal ideation present
        self.requires_intervention = (self.total_score >= 10 or self.q9_suicidal >= 1)
        
        self.save()
        return self.total_score
    
    def __str__(self):
        return f"{self.user.username} - PHQ-9: {self.total_score} ({self.severity}) - {self.completed_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'phq9_assessments'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', '-completed_at']),
            models.Index(fields=['severity']),
        ]


class GAD7Assessment(models.Model):
    """
    Generalized Anxiety Disorder-7 (GAD-7) for anxiety screening.
    Validated clinical scale for measuring anxiety severity.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gad7_assessments')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Assessment type
    assessment_type = models.CharField(max_length=20, choices=[
        ('baseline', 'Baseline'),
        ('follow_up', 'Follow-up'),
        ('weekly', 'Weekly Check-in'),
        ('crisis', 'Crisis Assessment')
    ], default='baseline')
    
    # GAD-7 Questions (0-3 scale: Not at all, Several days, More than half the days, Nearly every day)
    q1_nervous = models.IntegerField(help_text="Feeling nervous, anxious, or on edge")
    q2_control = models.IntegerField(help_text="Not being able to stop or control worrying")
    q3_worrying = models.IntegerField(help_text="Worrying too much about different things")
    q4_relaxing = models.IntegerField(help_text="Trouble relaxing")
    q5_restless = models.IntegerField(help_text="Being so restless that it's hard to sit still")
    q6_irritable = models.IntegerField(help_text="Becoming easily annoyed or irritable")
    q7_afraid = models.IntegerField(help_text="Feeling afraid as if something awful might happen")
    
    # Calculated fields
    total_score = models.IntegerField(help_text="Sum of all items (0-21)")
    severity = models.CharField(max_length=20, choices=[
        ('minimal', 'Minimal (0-4)'),
        ('mild', 'Mild (5-9)'),
        ('moderate', 'Moderate (10-14)'),
        ('severe', 'Severe (15-21)')
    ])
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    clinical_notes = models.TextField(blank=True)
    requires_intervention = models.BooleanField(default=False)
    
    def calculate_score(self):
        """Calculate total GAD-7 score and determine severity"""
        self.total_score = (
            self.q1_nervous + self.q2_control + self.q3_worrying + 
            self.q4_relaxing + self.q5_restless + self.q6_irritable + self.q7_afraid
        )
        
        # Determine severity
        if self.total_score <= 4:
            self.severity = 'minimal'
        elif self.total_score <= 9:
            self.severity = 'mild'
        elif self.total_score <= 14:
            self.severity = 'moderate'
        else:
            self.severity = 'severe'
        
        # Flag for intervention if moderate or higher
        self.requires_intervention = (self.total_score >= 10)
        
        self.save()
        return self.total_score
    
    def __str__(self):
        return f"{self.user.username} - GAD-7: {self.total_score} ({self.severity}) - {self.completed_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'gad7_assessments'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', '-completed_at']),
            models.Index(fields=['severity']),
        ]


class CBTThoughtRecord(models.Model):
    """
    Cognitive Behavioral Therapy Thought Records.
    Helps users identify and challenge negative automatic thoughts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='thought_records')
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # CBT Thought Record Components
    situation = models.TextField(help_text="What was happening? Where? When? With whom?")
    automatic_thoughts = models.TextField(help_text="What thoughts went through your mind?")
    emotions = models.JSONField(help_text="What emotions did you feel? Rate intensity 0-100", default=dict)
    
    # Cognitive distortions identified
    distortions = models.JSONField(help_text="Types of thinking errors", default=list)
    
    # Evidence and reframing
    evidence_for = models.TextField(blank=True, help_text="Evidence that supports the thought")
    evidence_against = models.TextField(blank=True, help_text="Evidence that contradicts the thought")
    alternative_thought = models.TextField(blank=True, help_text="More balanced perspective")
    
    # Outcome
    emotions_after = models.JSONField(help_text="Emotions after reframing (0-100)", default=dict)
    behavioral_response = models.TextField(blank=True, help_text="What action did you take?")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - Thought Record - {self.created_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'cbt_thought_records'
        ordering = ['-created_at']


class CBTBehavioralActivation(models.Model):
    """
    Behavioral Activation schedules for depression treatment.
    Evidence-based technique to increase engagement in rewarding activities.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavioral_activations')
    
    # Activity details
    activity_name = models.CharField(max_length=200)
    activity_description = models.TextField()
    activity_type = models.CharField(max_length=50, choices=[
        ('pleasure', 'Pleasure Activity'),
        ('mastery', 'Mastery Activity'),
        ('social', 'Social Activity'),
        ('physical', 'Physical Activity'),
        ('self_care', 'Self-Care')
    ])
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    
    # Predicted vs Actual ratings (0-10 scale)
    predicted_pleasure = models.IntegerField(help_text="Expected enjoyment (0-10)")
    predicted_mastery = models.IntegerField(help_text="Expected sense of accomplishment (0-10)")
    
    actual_pleasure = models.IntegerField(null=True, blank=True, help_text="Actual enjoyment (0-10)")
    actual_mastery = models.IntegerField(null=True, blank=True, help_text="Actual accomplishment (0-10)")
    
    # Completion tracking
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_notes = models.TextField(blank=True)
    
    # SDT Alignment (Self-Determination Theory)
    autonomy_support = models.BooleanField(default=True, help_text="User chose this activity")
    competence_building = models.BooleanField(default=False, help_text="Builds skills/confidence")
    relatedness_fostering = models.BooleanField(default=False, help_text="Involves social connection")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_name} - {self.scheduled_date}"
    
    class Meta:
        db_table = 'cbt_behavioral_activation'
        ordering = ['scheduled_date', 'scheduled_time']


class CBTExposureHierarchy(models.Model):
    """
    Exposure hierarchy for anxiety treatment.
    Systematic desensitization through graded exposure.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exposure_hierarchies')
    
    # Fear/anxiety target
    fear_target = models.CharField(max_length=200, help_text="What anxiety/fear are we addressing?")
    
    # Hierarchy details
    hierarchy_items = models.JSONField(help_text="List of exposure steps with SUDS ratings", default=list)
    # Format: [{"step": "...", "suds": 30, "completed": false, "date": null}, ...]
    # SUDS = Subjective Units of Distress Scale (0-100)
    
    # Progress tracking
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_exposure_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.fear_target} - Step {self.current_step}/{self.total_steps}"
    
    class Meta:
        db_table = 'cbt_exposure_hierarchy'
        ordering = ['-is_active', '-created_at']


class InterventionOutcome(models.Model):
    """
    Track intervention outcomes for research and effectiveness analysis.
    Enables pre-post comparison and effect size calculation.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='intervention_outcomes')
    
    # Intervention details
    intervention_type = models.CharField(max_length=50, choices=[
        ('cbt', 'Cognitive Behavioral Therapy'),
        ('behavioral_activation', 'Behavioral Activation'),
        ('exposure', 'Exposure Therapy'),
        ('thought_restructuring', 'Cognitive Restructuring'),
        ('combined', 'Combined Approach')
    ])
    
    # Baseline measurements
    baseline_phq9 = models.IntegerField(null=True, blank=True)
    baseline_gad7 = models.IntegerField(null=True, blank=True)
    baseline_date = models.DateTimeField()
    
    # Follow-up measurements
    followup_phq9 = models.IntegerField(null=True, blank=True)
    followup_gad7 = models.IntegerField(null=True, blank=True)
    followup_date = models.DateTimeField(null=True, blank=True)
    
    # Calculated outcomes
    phq9_change = models.FloatField(null=True, blank=True, help_text="Change in PHQ-9 score")
    gad7_change = models.FloatField(null=True, blank=True, help_text="Change in GAD-7 score")
    
    # Effect sizes (Cohen's d)
    phq9_effect_size = models.FloatField(null=True, blank=True)
    gad7_effect_size = models.FloatField(null=True, blank=True)
    
    # Clinical significance
    clinically_significant_change = models.BooleanField(default=False, help_text=">=50% symptom reduction")
    
    # Engagement metrics
    sessions_completed = models.IntegerField(default=0)
    thought_records_completed = models.IntegerField(default=0)
    activities_completed = models.IntegerField(default=0)
    
    # SDT Metrics
    autonomy_score = models.FloatField(null=True, blank=True, help_text="Perceived autonomy (1-7)")
    competence_score = models.FloatField(null=True, blank=True, help_text="Perceived competence (1-7)")
    relatedness_score = models.FloatField(null=True, blank=True, help_text="Perceived relatedness (1-7)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_changes(self):
        """Calculate change scores and effect sizes"""
        if self.baseline_phq9 and self.followup_phq9:
            self.phq9_change = self.baseline_phq9 - self.followup_phq9
            # Simple effect size (would need population SD for proper Cohen's d)
            if self.baseline_phq9 > 0:
                reduction_percent = (self.phq9_change / self.baseline_phq9) * 100
                self.clinically_significant_change = reduction_percent >= 50
        
        if self.baseline_gad7 and self.followup_gad7:
            self.gad7_change = self.baseline_gad7 - self.followup_gad7
        
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.intervention_type} - Outcome"
    
    class Meta:
        db_table = 'intervention_outcomes'
        ordering = ['-created_at']


class TheoreticalFramework(models.Model):
    """
    Document theoretical framework and mechanism of action.
    Combines Self-Determination Theory with CBT principles.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Core principles
    principles = models.JSONField(help_text="Core theoretical principles", default=dict)
    # Example: {"autonomy": "...", "competence": "...", "relatedness": "..."}
    
    # Mechanisms of action
    mechanisms = models.JSONField(help_text="How the intervention works", default=list)
    
    # Validated hypotheses
    hypotheses = models.JSONField(help_text="Testable hypotheses", default=list)
    
    # Supporting evidence
    evidence_base = models.TextField(help_text="Research citations and evidence")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'theoretical_frameworks'


class Feedback(models.Model):
    """Store user feedback submitted via feedback page"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks')
    rating = models.IntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    category = models.CharField(max_length=50, choices=[
        ('chatbot', 'AI Chatbot Experience'),
        ('ui', 'User Interface & Design'),
        ('features', 'Features & Functionality'),
        ('performance', 'Performance & Speed'),
        ('content', 'Content & Resources'),
        ('bug', 'Bug Report'),
        ('suggestion', 'Feature Suggestion'),
        ('other', 'Other')
    ])
    message = models.TextField()
    email = models.EmailField(blank=True, null=True)
    would_recommend = models.CharField(max_length=10, choices=[
        ('yes', 'Yes'),
        ('maybe', 'Maybe'),
        ('no', 'No')
    ], blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        user_display = self.user.username if self.user else self.email or "Anonymous"
        return f"{user_display} - {self.rating} stars - {self.category}"
    
    class Meta:
        db_table = 'feedbacks'
        ordering = ['-created_at']
