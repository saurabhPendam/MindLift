from django.urls import path
from . import views

urlpatterns = [
    # Page Views
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('verify-registration/', views.verify_registration, name='verify_registration'),
    path('resend-registration-otp/', views.resend_registration_otp, name='resend_registration_otp'),
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('complete-logout/', views.complete_logout, name='complete_logout'),
    path('feedback/', views.feedback_page, name='feedback'),
    path('chat/', views.chat, name='chat'),
    path('activities/', views.activities, name='activities'),
    path('quotes/', views.quotes, name='quotes'),
    path('reports/', views.reports, name='reports'),
    path('doctor/', views.doctor, name='doctor'),
    path('profile/', views.profile, name='profile'),
    
    # Chat API Endpoints
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/generate-report/', views.generate_report, name='generate_report'),
    path('api/get-report-detail/', views.get_report_detail, name='get_report_detail'),  # NEW
    path('api/chat-history/', views.get_chat_history, name='chat_history'),
    path('api/sentiment-trend/', views.get_sentiment_trend, name='sentiment_trend'),
    path('api/complete-activity/', views.complete_activity, name='complete_activity'),
    path('api/toggle-quote-favorite/', views.toggle_quote_favorite, name='toggle_quote_favorite'),
    
    # Conversation Management
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/delete-conversation/', views.delete_conversation, name='delete_conversation'),
    path('api/clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('api/new-conversation/', views.create_new_conversation, name='create_new_conversation'),
    path('api/check-llm-status/', views.check_llm_status, name='check_llm_status'),
    
    # Report Management
    path('api/delete-report/', views.delete_report, name='delete_report'),
    path('api/get-report-detail/', views.get_report_detail, name='get_report_detail'),
    
    # Account Management
    path('api/update-profile/', views.update_profile, name='update_profile'),
    path('api/request-account-deletion/', views.request_account_deletion, name='request_account_deletion'),
    path('api/cancel-account-deletion/', views.cancel_account_deletion, name='cancel_account_deletion'),
    path('api/delete-account-now/', views.delete_account_now, name='delete_account_now'),
    path('api/user-stats/', views.get_user_stats, name='get_user_stats'),
    
    # Feedback
    path('api/submit-feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Clinical Assessments
    path('assessments/phq9/', views.phq9_assessment, name='phq9_assessment'),
    path('assessments/gad7/', views.gad7_assessment, name='gad7_assessment'),
    path('assessments/progress/', views.assessment_progress, name='assessment_progress'),
    path('api/assessment-progress/', views.get_assessment_progress_api, name='get_assessment_progress_api'),
    
    # CBT Interventions
    path('cbt/thought-record/', views.cbt_thought_record, name='cbt_thought_record'),
    path('cbt/behavioral-activation/', views.cbt_behavioral_activation, name='cbt_behavioral_activation'),
    path('cbt/complete-activity/<int:activity_id>/', views.complete_behavioral_activation, name='complete_behavioral_activation'),
    path('api/cbt-suggestions/', views.get_cbt_suggestions, name='get_cbt_suggestions'),
]