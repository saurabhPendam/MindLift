from django.urls import path
from . import views

urlpatterns = [
    # Page Views
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/', views.chat, name='chat'),
    path('activities/', views.activities, name='activities'),
    path('quotes/', views.quotes, name='quotes'),
    path('reports/', views.reports, name='reports'),
    path('doctor/', views.doctor, name='doctor'),
    path('profile/', views.profile, name='profile'),
    
    # API Endpoints
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/generate-report/', views.generate_report, name='generate_report'),
    path('api/chat-history/', views.get_chat_history, name='chat_history'),
    path('api/sentiment-trend/', views.get_sentiment_trend, name='sentiment_trend'),
    path('api/complete-activity/', views.complete_activity, name='complete_activity'),
    path('api/toggle-quote-favorite/', views.toggle_quote_favorite, name='toggle_quote_favorite'),
    
    # NEW: Conversation Management Endpoints
    path('api/conversations/', views.get_conversations, name='get_conversations'),
    path('api/delete-conversation/', views.delete_conversation, name='delete_conversation'),
    path('api/clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('api/new-conversation/', views.create_new_conversation, name='create_new_conversation'),
    path('api/check-llm-status/', views.check_llm_status, name='check_llm_status'),
]