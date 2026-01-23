from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    UserProfile, Conversation, Message, SentimentReport,
    Activity, UserActivity, MotivationalQuote, UserQuoteFavorite,
    DoctorAppointment, AuditLog
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'gender', 'days_active_display', 'deletion_status', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['gender', 'deletion_requested', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'days_active_display']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone', 'date_of_birth', 'gender')
        }),
        ('Account Status', {
            'fields': ('deletion_requested', 'deletion_requested_at', 'deletion_scheduled_for')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'days_active_display'),
            'classes': ('collapse',)
        }),
    )
    
    def days_active_display(self, obj):
        return f"{obj.days_active()} days"
    days_active_display.short_description = 'Days Active'
    
    def deletion_status(self, obj):
        if obj.deletion_requested:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Deletion Scheduled</span>'
            )
        return format_html('<span style="color: green;">✓ Active</span>')
    deletion_status.short_description = 'Status'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'message_count_display', 'started_at', 'last_message_at', 'status_display']
    search_fields = ['user__username', 'title', 'session_id']
    list_filter = ['is_active', 'is_deleted', 'started_at']
    date_hierarchy = 'started_at'
    readonly_fields = ['session_id', 'started_at', 'last_message_at']
    
    def message_count_display(self, obj):
        return obj.message_count()
    message_count_display.short_description = 'Messages'
    
    def status_display(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">🗑️ Deleted</span>')
        elif obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: gray;">○ Inactive</span>')
    status_display.short_description = 'Status'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        'conversation', 'sender', 'content_preview', 
        'sentiment_display', 'safety_flags', 'timestamp'
    ]
    search_fields = ['content', 'conversation__user__username']
    list_filter = [
        'sender', 'sentiment_label', 'has_video', 
        'contains_crisis_keywords', 'requires_professional_referral', 
        'timestamp'
    ]
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'safety_analysis']
    
    fieldsets = (
        ('Message Details', {
            'fields': ('conversation', 'sender', 'content', 'timestamp')
        }),
        ('Sentiment Analysis', {
            'fields': ('sentiment_score', 'sentiment_label', 'emotions')
        }),
        ('AI Safety', {
            'fields': ('contains_crisis_keywords', 'requires_professional_referral', 'safety_analysis'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('has_video', 'video_url', 'model_used'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def sentiment_display(self, obj):
        if not obj.sentiment_label:
            return '-'
        
        colors = {
            'positive': 'green',
            'neutral': 'gray',
            'negative': 'red'
        }
        color = colors.get(obj.sentiment_label, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.sentiment_label.title()
        )
    sentiment_display.short_description = 'Sentiment'
    
    def safety_flags(self, obj):
        flags = []
        if obj.contains_crisis_keywords:
            flags.append('🚨 Crisis')
        if obj.requires_professional_referral:
            flags.append('⚕️ Professional')
        return ' '.join(flags) if flags else '-'
    safety_flags.short_description = 'Safety Flags'
    
    def safety_analysis(self, obj):
        analysis = []
        if obj.contains_crisis_keywords:
            analysis.append("⚠️ Contains crisis keywords - automated intervention triggered")
        if obj.requires_professional_referral:
            analysis.append("⚕️ Severely negative sentiment detected - professional help recommended")
        if obj.sentiment_score and obj.sentiment_score < -0.5:
            analysis.append(f"📊 Negative sentiment score: {obj.sentiment_score:.2f}")
        
        return "\n".join(analysis) if analysis else "No safety concerns detected"
    safety_analysis.short_description = 'Safety Analysis'


@admin.register(SentimentReport)
class SentimentReportAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'overall_sentiment', 'average_score', 
        'total_messages', 'date_range', 'deletion_status', 'created_at'
    ]
    search_fields = ['user__username']
    list_filter = ['overall_sentiment', 'is_deleted', 'created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%m/%d')} - {obj.end_date.strftime('%m/%d/%Y')}"
    date_range.short_description = 'Period'
    
    def deletion_status(self, obj):
        if obj.is_deleted:
            return format_html('<span style="color: red;">🗑️ Deleted</span>')
        return format_html('<span style="color: green;">✓ Active</span>')
    deletion_status.short_description = 'Status'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'duration_minutes', 'difficulty', 'is_active']
    search_fields = ['title', 'description']
    list_filter = ['category', 'difficulty', 'is_active']
    list_editable = ['is_active']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity', 'rating_display', 'completed_at']
    search_fields = ['user__username', 'activity__title']
    list_filter = ['rating', 'completed_at']
    date_hierarchy = 'completed_at'
    
    def rating_display(self, obj):
        if obj.rating:
            stars = '⭐' * obj.rating
            return f"{stars} ({obj.rating}/5)"
        return '-'
    rating_display.short_description = 'Rating'


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
    list_display = ['user', 'quote_preview', 'favorited_at']
    search_fields = ['user__username', 'quote__quote']
    date_hierarchy = 'favorited_at'
    
    def quote_preview(self, obj):
        return obj.quote.quote[:40] + '...' if len(obj.quote.quote) > 40 else obj.quote.quote
    quote_preview.short_description = 'Quote'


@admin.register(DoctorAppointment)
class DoctorAppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'doctor_name', 'appointment_date', 'status', 'duration_minutes']
    search_fields = ['user__username', 'doctor_name']
    list_filter = ['status', 'appointment_date']
    date_hierarchy = 'appointment_date'
    list_editable = ['status']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'action', 'category', 'timestamp', 'ip_address']
    search_fields = ['user__username', 'action', 'description']
    list_filter = ['category', 'timestamp']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'full_description']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'action', 'category', 'timestamp')
        }),
        ('Details', {
            'fields': ('full_description', 'ip_address', 'user_agent')
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return 'Anonymous'
    user_display.short_description = 'User'
    
    def full_description(self, obj):
        return obj.description
    full_description.short_description = 'Description'
    
    def has_add_permission(self, request):
        # Prevent manual creation of audit logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of audit logs
        return False


# Customize admin site
admin.site.site_header = "MindLift Admin Panel"
admin.site.site_title = "MindLift Admin"
admin.site.index_title = "Mental Health Chatbot Management" 