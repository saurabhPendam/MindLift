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
import uuid
import logging

from .models import (
    UserProfile, Conversation, Message, SentimentReport,
    Activity, UserActivity, MotivationalQuote, UserQuoteFavorite,
    DoctorAppointment
)
from .sentiment_service import SentimentAnalyzer, ReportGenerator
from .llm_service import llm_service

logger = logging.getLogger(__name__)


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
            logger.error(f"Registration error: {str(e)}")
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
    """Main chat interface with session management - FIXED"""
    # Get session_id from query parameter
    session_id = request.GET.get('session_id')
    
    conversation = None
    
    if session_id:
        # Load existing conversation ONLY
        try:
            conversation = Conversation.objects.get(
                session_id=session_id,
                user=request.user,
                is_deleted=False
            )
        except Conversation.DoesNotExist:
            # If session_id is invalid, redirect to chat page without session_id
            return redirect('chat')
    
    # Get recent messages if conversation exists
    recent_messages = []
    if conversation:
        recent_messages = Message.objects.filter(
            conversation=conversation
        ).order_by('timestamp')[:50]
    
    # Get all user's conversations for sidebar
    all_conversations = Conversation.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-last_message_at')[:20]
    
    return render(request, 'chat.html', {
        'username': request.user.username,
        'conversation_id': conversation.id if conversation else None,
        'session_id': str(conversation.session_id) if conversation else None,
        'recent_messages': recent_messages,
        'all_conversations': all_conversations,
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
    user_reports = SentimentReport.objects.filter(user=request.user).order_by('-created_at')[:10]
    
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
    """
    API endpoint to send message and get LLM response
    Uses Hybrid LLM (MindLift -> Phi -> RASA -> Rule-based fallback)
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create conversation using session_id
        conversation = None
        if session_id:
            try:
                conversation = Conversation.objects.get(
                    session_id=session_id,
                    user=request.user,
                    is_deleted=False
                )
            except Conversation.DoesNotExist:
                pass
        
        # Create NEW conversation ONLY if none exists
        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                title=user_message[:50]  # Use first message as title
            )
            logger.info(f"✅ Created new conversation: {conversation.session_id}")
        
        # Save user message
        user_msg = Message.objects.create(
            conversation=conversation,
            sender='user',
            content=user_message
        )
        
        # Analyze sentiment
        analyzer = SentimentAnalyzer()
        try:
            sentiment_result = analyzer.analyze_message(user_msg)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            sentiment_result = {'label': 'neutral', 'score': 0.0}
        
        # Get conversation context (last 4 messages for speed)
        context_messages = Message.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')[:4]
        
        context = [
            {
                'sender': msg.sender,
                'content': msg.content
            }
            for msg in reversed(list(context_messages))
        ]
        
        # Send to Hybrid LLM (MindLift -> Phi -> RASA -> Rule-based)
        sender_id = f"user_{request.user.id}"
        
        try:
            logger.info("🚀 Sending message to LLM service")
            llm_responses = llm_service.send_message(user_message, sender_id, context)
        except Exception as e:
            logger.error(f"LLM service error: {str(e)}")
            # Emergency fallback
            llm_responses = [{
                'text': "I'm here to listen and support you. Please tell me more about how you're feeling.",
                'youtube_url': None,
                'model': 'emergency_fallback',
                'source': 'error_handler',
                'success': True
            }]
        
        # Save bot responses
        bot_messages = []
        for response in llm_responses:
            bot_text = response.get('text', '')
            youtube_url = response.get('youtube_url')
            model_used = response.get('model', 'unknown')
            
            if bot_text or youtube_url:
                bot_msg = Message.objects.create(
                    conversation=conversation,
                    sender='bot',
                    content=bot_text,
                    has_video=bool(youtube_url),
                    video_url=youtube_url,
                    model_used=model_used
                )
                bot_messages.append({
                    'id': bot_msg.id,
                    'text': bot_text,
                    'youtube_url': youtube_url,
                    'timestamp': bot_msg.timestamp.isoformat(),
                })
        
        # Update conversation timestamp and title if first message
        conversation.last_message_at = timezone.now()
        if conversation.message_count() == 2:  # First user message + first bot response
            conversation.title = user_message[:50]
        conversation.save()
        
        logger.info(f"✅ Message processed successfully. Model: {llm_responses[0].get('model', 'unknown')}")
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'text': user_message,
                'sentiment': sentiment_result.get('label', 'neutral'),
                'score': sentiment_result.get('score', 0.0),
                'timestamp': user_msg.timestamp.isoformat()
            },
            'bot_messages': bot_messages,
            'conversation_id': conversation.id,
            'session_id': str(conversation.session_id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Send message error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An error occurred. Please try again.'}, status=500)


@login_required
@require_http_methods(["POST"])
def generate_report(request):
    """Generate sentiment analysis report"""
    try:
        data = json.loads(request.body)
        days = data.get('days', 7)
        session_id = data.get('session_id')
        
        generator = ReportGenerator()
        
        if session_id:
            try:
                conversation = Conversation.objects.get(
                    session_id=session_id,
                    user=request.user,
                    is_deleted=False
                )
                report = generator.generate_conversation_report(conversation, request.user)
            except Conversation.DoesNotExist:
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            report = generator.generate_user_report(request.user, days=days)
        
        return JsonResponse({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Generate report error: {str(e)}", exc_info=True)
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
        logger.error(f"Get sentiment trend error: {str(e)}")
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
        logger.error(f"Complete activity error: {str(e)}")
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
        logger.error(f"Toggle quote favorite error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_chat_history(request):
    """Get chat history"""
    try:
        session_id = request.GET.get('session_id')
        limit = int(request.GET.get('limit', 50))
        
        if session_id:
            conversation = get_object_or_404(
                Conversation,
                session_id=session_id,
                user=request.user,
                is_deleted=False
            )
            messages_list = Message.objects.filter(conversation=conversation)
        else:
            messages_list = Message.objects.filter(
                conversation__user=request.user,
                conversation__is_deleted=False
            )
        
        messages_list = messages_list.order_by('-timestamp')[:limit]
        
        messages_data = [{
            'id': msg.id,
            'sender': msg.sender,
            'content': msg.content,
            'sentiment': msg.sentiment_label,
            'has_video': msg.has_video,
            'video_url': msg.video_url,
            'timestamp': msg.timestamp.isoformat(),
            'session_id': str(msg.conversation.session_id)
        } for msg in reversed(messages_list)]
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        logger.error(f"Get chat history error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_conversations(request):
    """Get all conversations for the user"""
    try:
        conversations = Conversation.objects.filter(
            user=request.user,
            is_deleted=False
        ).order_by('-last_message_at')[:50]
        
        conversations_data = [{
            'id': conv.id,
            'session_id': str(conv.session_id),
            'title': conv.title,
            'started_at': conv.started_at.isoformat(),
            'last_message_at': conv.last_message_at.isoformat(),
            'message_count': conv.message_count(),
            'is_active': conv.is_active
        } for conv in conversations]
        
        return JsonResponse({
            'success': True,
            'conversations': conversations_data
        })
        
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_conversation(request):
    """Delete (soft delete) a conversation"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        conversation = get_object_or_404(
            Conversation,
            session_id=session_id,
            user=request.user
        )
        
        # Soft delete
        conversation.soft_delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def clear_conversation(request):
    """Clear all messages in a conversation"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        conversation = get_object_or_404(
            Conversation,
            session_id=session_id,
            user=request.user,
            is_deleted=False
        )
        
        # Delete all messages
        Message.objects.filter(conversation=conversation).delete()
        
        # Reset title
        conversation.title = "New Conversation"
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Conversation cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear conversation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_new_conversation(request):
    """Create a new conversation session - FIXED"""
    try:
        # Always create a fresh conversation
        conversation = Conversation.objects.create(
            user=request.user,
            title="New Conversation"
        )
        
        logger.info(f"✅ New conversation created: {conversation.session_id}")
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'session_id': str(conversation.session_id),
            'message': 'New conversation created'
        })
        
    except Exception as e:
        logger.error(f"Create new conversation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def check_llm_status(request):
    """Check status of all LLM services (Ollama MindLift, Phi, RASA)"""
    try:
        status = llm_service.get_status()
        
        ollama = status.get('ollama', {})
        rasa = status.get('rasa', {})
        
        # Build user-friendly messages
        messages = []
        
        # Check primary model (MindLift)
        if ollama.get('available') and ollama.get('primary_available'):
            messages.append(f"✅ Primary model '{ollama.get('primary_model')}' is ready")
        elif ollama.get('available'):
            messages.append(f"⚠️ Primary model '{ollama.get('primary_model')}' not found")
        else:
            messages.append(f"❌ Ollama not available: {ollama.get('error', 'Unknown error')}")
        
        # Check fallback model (Phi)
        if ollama.get('available') and ollama.get('fallback_available'):
            messages.append(f"✅ Fallback model '{ollama.get('fallback_model')}' is ready")
        elif ollama.get('available'):
            messages.append(f"⚠️ Fallback model '{ollama.get('fallback_model')}' not found")
        
        # Check RASA
        if rasa.get('available'):
            messages.append("✅ RASA server is running")
        else:
            messages.append("⚠️ RASA server not available (using rule-based fallback)")
        
        # Show available models if Ollama is running
        if ollama.get('available') and ollama.get('installed_models'):
            messages.append(f"📦 Available models: {', '.join(ollama.get('installed_models', []))}")
        
        return JsonResponse({
            'success': True,
            'status': status,
            'messages': messages,
            'primary_service': status.get('primary_service'),
            'primary_model_ready': ollama.get('available', False) and ollama.get('primary_available', False),
            'fallback_model_ready': ollama.get('available', False) and ollama.get('fallback_available', False),
            'rasa_ready': rasa.get('available', False)
        })
        
    except Exception as e:
        logger.error(f"Check LLM status error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'messages': ['❌ Error checking service status']
        }, status=500)
