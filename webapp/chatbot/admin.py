from django.contrib import admin
from .models import (
    UserProfile, Conversation, Message, SentimentReport,
    Activity, UserActivity, MotivationalQuote, UserQuoteFavorite,
    DoctorAppointment
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'gender', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['gender', 'created_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'started_at', 'last_message_at', 'is_active']
    search_fields = ['user__username', 'title']
    list_filter = ['is_active', 'started_at']
    date_hierarchy = 'started_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'sender', 'content_preview', 'sentiment_label', 'timestamp']
    search_fields = ['content', 'conversation__user__username']
    list_filter = ['sender', 'sentiment_label', 'has_video', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(SentimentReport)
class SentimentReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'overall_sentiment', 'average_score', 'total_messages', 'start_date', 'end_date', 'created_at']
    search_fields = ['user__username']
    list_filter = ['overall_sentiment', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'duration_minutes', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    list_filter = ['category', 'difficulty', 'is_active']
    list_editable = ['is_active']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'rating', 'completed_at']
    search_fields = ['user__username', 'activity__title']
    list_filter = ['rating', 'completed_at']
    date_hierarchy = 'completed_at'


@admin.register(MotivationalQuote)
class MotivationalQuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_preview', 'author', 'category', 'is_active']
    search_fields = ['quote', 'author']
    list_filter = ['category', 'is_active']
    list_editable = ['is_active']
    
    def quote_preview(self, obj):
        return obj.quote[:60] + '...' if len(obj.quote) > 60 else obj.quote
    quote_preview.short_description = 'Quote'


@admin.register(UserQuoteFavorite)
class UserQuoteFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'quote', 'favorited_at']
    search_fields = ['user__username', 'quote__quote']
    date_hierarchy = 'favorited_at'


@admin.register(DoctorAppointment)
class DoctorAppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'doctor_name', 'appointment_date', 'status', 'duration_minutes']
    search_fields = ['user__username', 'doctor_name']
    list_filter = ['status', 'appointment_date']
    date_hierarchy = 'appointment_date'
    list_editable = ['status']