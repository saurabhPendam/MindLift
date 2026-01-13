from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

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

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        db_table = 'user_profiles'


class Conversation(models.Model):
    """Store conversation sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, default="New Conversation")
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
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
    sentiment_score = models.FloatField(null=True, blank=True)  # VADER compound score
    sentiment_label = models.CharField(max_length=20, null=True, blank=True)  # positive, negative, neutral
    
    # NRC Emotions
    emotions = models.JSONField(default=dict, blank=True)  # Store NRC emotion scores
    
    # Metadata
    has_video = models.BooleanField(default=False)
    video_url = models.URLField(null=True, blank=True)
    
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
    overall_sentiment = models.CharField(max_length=20)  # positive, negative, neutral
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - Report {self.created_at.strftime('%Y-%m-%d')}"
    
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