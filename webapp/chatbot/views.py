from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import (
    UserProfile, Conversation, Message, SentimentReport,
    Activity, UserActivity, MotivationalQuote, UserQuoteFavorite
)
from .sentiment_service import SentimentAnalyzer, ReportGenerator, extract_youtube_url
from .rasa_integration import rasa_service, message_processor


# ============================================
# PAGE VIEWS
# ============================================

def home(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('chat')
    return render(request, 'home.html')


def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not username or not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'register.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'register.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'register.html')
        
        try:
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            # Create user profile
            UserProfile.objects.create(user=user)
            
            login(request, user)
            messages.success(request, f'Welcome to MindLift, {username}!')
            return redirect('chat')
        except Exception as e:
            messages.error(request, 'Registration failed. Please try again.')
            return render(request, 'register.html')
    
    return render(request, 'register.html')


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('chat')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')


@login_required
def chat(request):
    """Main chat interface"""
    # Get or create active conversation
    conversation = Conversation.objects.filter(
        user=request.user,
        is_active=True
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create(
            user=request.user,
            title="New Conversation"
        )
    
    # Get recent messages
    recent_messages = Message.objects.filter(
        conversation=conversation
    ).order_by('-timestamp')[:50]
    
    return render(request, 'chat.html', {
        'username': request.user.username,
        'conversation_id': conversation.id,
        'recent_messages': reversed(recent_messages)
    })


@login_required
def activities(request):
    """Activities page for mood improvement"""
    categories = Activity.objects.values_list('category', flat=True).distinct()
    
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        activities_list = Activity.objects.filter(
            is_active=True,
            category=selected_category
        )
    else:
        activities_list = Activity.objects.filter(is_active=True)
    
    # Get user's completed activities
    completed = UserActivity.objects.filter(
        user=request.user
    ).values_list('activity_id', flat=True)
    
    return render(request, 'activities.html', {
        'activities': activities_list,
        'categories': categories,
        'selected_category': selected_category,
        'completed_ids': list(completed)
    })


@login_required
def quotes(request):
    """Motivational quotes page"""
    categories = MotivationalQuote.objects.values_list('category', flat=True).distinct()
    
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        quotes_list = MotivationalQuote.objects.filter(
            is_active=True,
            category=selected_category
        )
    else:
        quotes_list = MotivationalQuote.objects.filter(is_active=True)
    
    # Get random quote for display
    daily_quote = quotes_list.order_by('?').first()
    
    # Get user's favorite quotes
    favorites = UserQuoteFavorite.objects.filter(
        user=request.user
    ).values_list('quote_id', flat=True)
    
    return render(request, 'quotes.html', {
        'quotes': quotes_list,
        'categories': categories,
        'selected_category': selected_category,
        'daily_quote': daily_quote,
        'favorite_ids': list(favorites)
    })


@login_required
def reports(request):
    """Sentiment analysis reports page"""
    user_reports = SentimentReport.objects.filter(user=request.user)[:10]
    
    return render(request, 'reports.html', {
        'reports': user_reports
    })


@login_required
def doctor(request):
    """Doctor consultation page"""
    return render(request, 'doctor.html', {
        'username': request.user.username
    })


@login_required
def profile(request):
    """User profile page"""
    return render(request, 'profile.html', {
        'username': request.user.username,
        'email': request.user.email
    })


# ============================================
# API ENDPOINTS
# ============================================

@login_required
@require_http_methods(["POST"])
def send_message(request):
    """API endpoint to send message and get RASA response"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create conversation
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title=user_message[:50]
            )
        
        # Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )
        
        # Analyze sentiment
        analyzer = SentimentAnalyzer()
        sentiment_result = analyzer.analyze_message(user_msg)
        
        # Send to RASA
        sender_id = f"user_{request.user.id}"
        rasa_responses = rasa_service.send_message(user_message, sender_id)
        
        # Process RASA responses
        processed_responses = message_processor.process_responses(rasa_responses)
        
        # Save bot responses
        bot_messages = []
        for response in processed_responses:
            bot_text = response.get('text', '')
            
            # Check for YouTube URL
            youtube_url = response.get('youtube_url')
            
            if bot_text or youtube_url:
                bot_msg = Message.objects.create(
                    conversation=conversation,
                    sender='bot',
                    content=bot_text,
                    has_video=bool(youtube_url),
                    video_url=youtube_url
                )
                bot_messages.append({
                    'id': bot_msg.id,
                    'text': bot_text,
                    'youtube_url': youtube_url,
                    'timestamp': bot_msg.timestamp.isoformat(),
                    'buttons': response.get('buttons', []),
                    'image': response.get('image')
                })
        
        # Update conversation timestamp
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'text': user_message,
                'sentiment': sentiment_result['label'],
                'score': sentiment_result['score'],
                'timestamp': user_msg.timestamp.isoformat()
            },
            'bot_messages': bot_messages,
            'conversation_id': conversation.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def generate_report(request):
    """Generate sentiment analysis report"""
    try:
        data = json.loads(request.body)
        days = data.get('days', 7)
        conversation_id = data.get('conversation_id')
        
        generator = ReportGenerator()
        
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            report = generator.generate_conversation_report(conversation, request.user)
        else:
            report = generator.generate_user_report(request.user, days=days)
        
        return JsonResponse({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_sentiment_trend(request):
    """Get sentiment trend over time"""
    try:
        days = int(request.GET.get('days', 30))
        
        generator = ReportGenerator()
        trend = generator.get_user_sentiment_trend(request.user, days=days)
        
        return JsonResponse({
            'success': True,
            'trend': trend
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def complete_activity(request):
    """Mark activity as completed"""
    try:
        data = json.loads(request.body)
        activity_id = data.get('activity_id')
        rating = data.get('rating')
        notes = data.get('notes', '')
        
        activity = get_object_or_404(Activity, id=activity_id)
        
        user_activity = UserActivity.objects.create(
            user=request.user,
            activity=activity,
            rating=rating,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Activity completed!',
            'activity_id': activity_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_quote_favorite(request):
    """Add or remove quote from favorites"""
    try:
        data = json.loads(request.body)
        quote_id = data.get('quote_id')
        
        quote = get_object_or_404(MotivationalQuote, id=quote_id)
        
        favorite, created = UserQuoteFavorite.objects.get_or_create(
            user=request.user,
            quote=quote
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({
                'success': True,
                'favorited': False,
                'message': 'Quote removed from favorites'
            })
        else:
            return JsonResponse({
                'success': True,
                'favorited': True,
                'message': 'Quote added to favorites'
            })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_chat_history(request):
    """Get chat history for a conversation"""
    try:
        conversation_id = request.GET.get('conversation_id')
        limit = int(request.GET.get('limit', 50))
        
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            messages_list = Message.objects.filter(conversation=conversation)
        else:
            messages_list = Message.objects.filter(conversation__user=request.user)
        
        messages_list = messages_list.order_by('-timestamp')[:limit]
        
        messages_data = [{
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'sentiment': msg.sentiment_label,
            'has_video': msg.has_video,
            'video_url': msg.video_url,
            'timestamp': msg.timestamp.isoformat()
        } for msg in reversed(messages_list)]
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def check_rasa_status(request):
    """Check if RASA server is running"""
    is_running = rasa_service.check_health()
    
    return JsonResponse({
        'success': True,
        'rasa_running': is_running,
        'message': 'RASA server is running' if is_running else 'RASA server is not available'
    })