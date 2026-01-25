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
    DoctorAppointment, AuditLog
)
from .sentiment_service import SentimentAnalyzer, ReportGenerator
from .groq_service import groq_service

logger = logging.getLogger(__name__)


# ============================================
# HELPER FUNCTIONS
# ============================================

def log_audit(user, action, description, request=None, category='account'):
    """Create audit log entry"""
    ip_address = None
    user_agent = ''
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        category=category
    )


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
            UserProfile.objects.create(user=user)
            
            # Log registration
            log_audit(user, 'account_created', f'New account registered: {username}', request, 'account')
            
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
            # Check if account deletion is pending
            try:
                profile = user.profile
                if profile.deletion_requested:
                    messages.warning(request, 
                        f'Your account deletion is scheduled for {profile.deletion_scheduled_for.strftime("%Y-%m-%d")}. '
                        'You can cancel it from your profile settings.')
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)
            
            login(request, user)
            log_audit(user, 'login', f'User logged in: {username}', request, 'security')
            messages.success(request, f'Welcome back, {username}!')
            return redirect('chat')
        else:
            log_audit(None, 'failed_login', f'Failed login attempt for username: {username}', request, 'security')
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def logout_view(request):
    """User logout"""
    if request.user.is_authenticated:
        log_audit(request.user, 'logout', f'User logged out: {request.user.username}', request, 'security')
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')


@login_required
def chat(request):
    """Main chat interface"""
    session_id = request.GET.get('session_id')
    conversation = None
    
    if session_id:
        try:
            conversation = Conversation.objects.get(
                session_id=session_id,
                user=request.user,
                is_deleted=False
            )
        except Conversation.DoesNotExist:
            return redirect('chat')
    
    recent_messages = []
    if conversation:
        recent_messages = Message.objects.filter(
            conversation=conversation
        ).order_by('timestamp')[:50]
    
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
def profile(request):
    """Profile page with account management"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    # Calculate statistics
    total_conversations = Conversation.objects.filter(
        user=request.user, 
        is_deleted=False
    ).count()
    
    total_messages = Message.objects.filter(
        conversation__user=request.user,
        conversation__is_deleted=False,
        sender='user'
    ).count()
    
    days_active = profile.days_active()
    
    # Get recent sentiment
    recent_report = SentimentReport.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at').first()
    
    overall_mood = recent_report.overall_sentiment if recent_report else 'neutral'
    
    return render(request, 'profile.html', {
        'username': request.user.username,
        'email': request.user.email,
        'profile': profile,
        'days_active': days_active,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'overall_mood': overall_mood,
        'deletion_pending': profile.deletion_requested,
        'deletion_date': profile.deletion_scheduled_for
    })


@login_required
def reports(request):
    """Reports page - only show non-deleted reports"""
    user_reports = SentimentReport.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')[:10]
    
    return render(request, 'reports.html', {'reports': user_reports})


# ============================================
# ACCOUNT MANAGEMENT API
# ============================================

@login_required
@require_http_methods(["POST"])
def request_account_deletion(request):
    """Request account deletion with grace period"""
    try:
        data = json.loads(request.body)
        grace_period_days = data.get('grace_period_days', 30)
        
        profile = request.user.profile
        profile.request_deletion(grace_period_days)
        
        log_audit(
            request.user,
            'account_deletion_requested',
            f'User requested account deletion with {grace_period_days} days grace period',
            request,
            'deletion'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Account deletion scheduled for {profile.deletion_scheduled_for.strftime("%Y-%m-%d")}',
            'deletion_date': profile.deletion_scheduled_for.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Account deletion request error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cancel_account_deletion(request):
    """Cancel pending account deletion"""
    try:
        profile = request.user.profile
        
        if not profile.deletion_requested:
            return JsonResponse({'error': 'No pending deletion request'}, status=400)
        
        profile.cancel_deletion()
        
        log_audit(
            request.user,
            'account_deletion_cancelled',
            'User cancelled account deletion request',
            request,
            'account'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Account deletion cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"Cancel deletion error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_account_now(request):
    """Immediately delete account (skip grace period)"""
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        
        # Verify password
        if not request.user.check_password(password):
            return JsonResponse({'error': 'Invalid password'}, status=400)
        
        username = request.user.username
        user_id = request.user.id
        
        # Log deletion before deleting
        log_audit(
            request.user,
            'account_deleted',
            f'User {username} permanently deleted their account',
            request,
            'deletion'
        )
        
        # Delete user (cascades to all related data)
        request.user.delete()
        
        logger.info(f"Account deleted: {username} (ID: {user_id})")
        
        return JsonResponse({
            'success': True,
            'message': 'Account deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Account deletion error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


# ============================================
# REPORT MANAGEMENT API
# ============================================

@login_required
@require_http_methods(["POST"])
def delete_report(request):
    """Soft delete a sentiment report"""
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        
        if not report_id:
            return JsonResponse({'error': 'report_id is required'}, status=400)
        
        report = get_object_or_404(
            SentimentReport,
            id=report_id,
            user=request.user,
            is_deleted=False
        )
        
        report.soft_delete()
        
        log_audit(
            request.user,
            'report_deleted',
            f'Sentiment report {report_id} deleted',
            request,
            'deletion'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Report deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Report deletion error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_stats(request):
    """Get user statistics for profile"""
    try:
        profile = request.user.profile
        
        stats = {
            'days_active': profile.days_active(),
            'total_conversations': Conversation.objects.filter(
                user=request.user,
                is_deleted=False
            ).count(),
            'total_messages': Message.objects.filter(
                conversation__user=request.user,
                conversation__is_deleted=False,
                sender='user'
            ).count(),
            'total_reports': SentimentReport.objects.filter(
                user=request.user,
                is_deleted=False
            ).count(),
            'completed_activities': UserActivity.objects.filter(
                user=request.user
            ).count(),
            'favorite_quotes': UserQuoteFavorite.objects.filter(
                user=request.user
            ).count()
        }
        
        # Get recent sentiment
        recent_report = SentimentReport.objects.filter(
            user=request.user,
            is_deleted=False
        ).order_by('-created_at').first()
        
        if recent_report:
            stats['overall_mood'] = recent_report.overall_sentiment
            stats['mood_score'] = round(recent_report.average_score, 2)
        else:
            stats['overall_mood'] = 'neutral'
            stats['mood_score'] = 0.0
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def activities(request):
    """Activities page"""
    categories = Activity.objects.values_list('category', flat=True).distinct()
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        activities_list = Activity.objects.filter(is_active=True, category=selected_category)
    else:
        activities_list = Activity.objects.filter(is_active=True)
    
    completed = UserActivity.objects.filter(user=request.user).values_list('activity_id', flat=True)
    
    return render(request, 'activities.html', {
        'activities': activities_list,
        'categories': categories,
        'selected_category': selected_category,
        'completed_ids': list(completed)
    })


@login_required
def quotes(request):
    """Quotes page"""
    categories = MotivationalQuote.objects.values_list('category', flat=True).distinct()
    selected_category = request.GET.get('category', '')
    
    if selected_category:
        quotes_list = MotivationalQuote.objects.filter(is_active=True, category=selected_category)
    else:
        quotes_list = MotivationalQuote.objects.filter(is_active=True)
    
    daily_quote = quotes_list.order_by('?').first()
    favorites = UserQuoteFavorite.objects.filter(user=request.user).values_list('quote_id', flat=True)
    
    return render(request, 'quotes.html', {
        'quotes': quotes_list,
        'categories': categories,
        'selected_category': selected_category,
        'daily_quote': daily_quote,
        'favorite_ids': list(favorites)
    })


@login_required
def doctor(request):
    """Doctor consultation page"""
    return render(request, 'doctor.html', {'username': request.user.username})


# ============================================
# CHAT API ENDPOINTS
# ============================================
# Replace the send_message function in views.py with this:

@login_required
@require_http_methods(["POST"])
def send_message(request):
    """
    API endpoint to send message - Uses Hybrid RASA + Groq system
    """
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        use_rasa = data.get('use_rasa', True)  # Allow frontend to toggle
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get or create conversation
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
        
        if not conversation:
            conversation = Conversation.objects.create(
                user=request.user,
                title=user_message[:50]
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
        
        # Get conversation context
        context_messages = Message.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')[:4]
        
        context = [
            {'sender': msg.sender, 'content': msg.content}
            for msg in reversed(list(context_messages))
        ]
        
        # === HYBRID SYSTEM: Use RASA + Groq ===
        from .hybrid_service import hybrid_service
        
        try:
            logger.info("🚀 Processing message through Hybrid System")
            
            # Process through hybrid system
            bot_response = hybrid_service.process_message(
                message=user_message,
                user_id=str(request.user.id),
                context=context
            )
            
            if not bot_response or not bot_response.get('success'):
                raise Exception("Hybrid system returned unsuccessful response")
            
            # Extract response components
            bot_text = bot_response.get('text', '')
            video_info = bot_response.get('video')
            response_source = bot_response.get('source', 'unknown')
            intent = bot_response.get('intent')
            confidence = bot_response.get('confidence')
            
            # Log which system was used
            logger.info(f"✅ Response from: {response_source}")
            if intent:
                logger.info(f"📊 Intent: {intent} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Hybrid system error: {str(e)}")
            # Ultimate fallback
            bot_text = "I'm here to listen and support you. Please tell me more about how you're feeling."
            video_info = None
            response_source = 'emergency_fallback'
        
        # Prepare video data
        video_embed_url = None
        video_watch_url = None
        video_title = None
        
        if video_info:
            video_embed_url = video_info.get('embed_url')
            video_watch_url = video_info.get('watch_url')
            video_title = video_info.get('title', 'Recommended Video')
        
        # Save bot response
        bot_msg = Message.objects.create(
            conversation=conversation,
            sender='bot',
            content=bot_text,
            has_video=bool(video_info),
            video_url=video_embed_url,
            model_used=response_source
        )
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        if conversation.message_count() == 2:
            conversation.title = user_message[:50]
        conversation.save()
        
        logger.info(f"✅ Message processed. Source: {response_source}")
        
        return JsonResponse({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'text': user_message,
                'sentiment': sentiment_result.get('label', 'neutral'),
                'score': sentiment_result.get('score', 0.0),
                'timestamp': user_msg.timestamp.isoformat()
            },
            'bot_messages': [{
                'id': bot_msg.id,
                'text': bot_text,
                'video': {
                    'embed_url': video_embed_url,
                    'watch_url': video_watch_url,
                    'title': video_title,
                    'has_video': bool(video_info)
                } if video_info else None,
                'timestamp': bot_msg.timestamp.isoformat(),
                'source': response_source,
                'intent': intent
            }],
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
    """Generate sentiment analysis report - FIXED VERSION with proper score calculation"""
    try:
        data = json.loads(request.body)
        days = data.get('days', 7)
        session_id = data.get('session_id')
        
        logger.info(f"Generating report for user {request.user.username}, days={days}, session_id={session_id}")
        
        generator = ReportGenerator()
        
        # Check if user has any messages first
        total_messages = Message.objects.filter(
            conversation__user=request.user,
            sender='user',
            conversation__is_deleted=False
        ).count()
        
        logger.info(f"Total user messages: {total_messages}")
        
        if total_messages == 0:
            logger.warning("No messages found for user")
            return JsonResponse({
                'success': False,
                'error': 'No messages found. Start chatting to generate a report!'
            }, status=400)
        
        if session_id:
            try:
                conversation = Conversation.objects.get(
                    session_id=session_id,
                    user=request.user,
                    is_deleted=False
                )
                
                # Check if conversation has user messages
                conv_messages = Message.objects.filter(
                    conversation=conversation,
                    sender='user'
                ).count()
                
                logger.info(f"Conversation {session_id} has {conv_messages} user messages")
                
                if conv_messages == 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'This conversation has no messages to analyze.'
                    }, status=400)
                
                logger.info(f"Generating conversation report for {conversation.id}")
                report = generator.generate_conversation_report(conversation, request.user)
                
            except Conversation.DoesNotExist:
                logger.error(f"Conversation {session_id} not found")
                return JsonResponse({'error': 'Conversation not found'}, status=404)
        else:
            logger.info(f"Generating user report for last {days} days")
            report = generator.generate_user_report(request.user, days=days)
        
        # Check if report generation was successful
        if 'error' in report:
            logger.error(f"Report generation error: {report['error']}")
            return JsonResponse({
                'success': False,
                'error': report['error']
            }, status=400)
        
        # Log the generated report details
        logger.info(f"Report generated successfully:")
        logger.info(f"  - Report ID: {report.get('report_id')}")
        logger.info(f"  - Average Score: {report.get('average_score')}")
        logger.info(f"  - Overall Sentiment: {report.get('overall_sentiment')}")
        logger.info(f"  - Total Messages: {report.get('total_messages')}")
        logger.info(f"  - Positive: {report.get('positive', {}).get('count')} ({report.get('positive', {}).get('percentage')}%)")
        logger.info(f"  - Neutral: {report.get('neutral', {}).get('count')} ({report.get('neutral', {}).get('percentage')}%)")
        logger.info(f"  - Negative: {report.get('negative', {}).get('count')} ({report.get('negative', {}).get('percentage')}%)")
        
        log_audit(
            request.user,
            'report_generated',
            f'Sentiment report generated for {days} days',
            request,
            'data'
        )
        
        return JsonResponse({'success': True, 'report': report})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Generate report error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate report. Please try again.'
        }, status=500)  

@login_required
@require_http_methods(["GET"])
def get_report_detail(request):
    """
    Get detailed report data for modal view - COMPLETE FIXED VERSION
    Returns comprehensive report including summary, emotions, and recommendations
    """
    try:
        report_id = request.GET.get('report_id')
        
        if not report_id:
            return JsonResponse({'error': 'report_id is required'}, status=400)
        
        report = get_object_or_404(
            SentimentReport,
            id=report_id,
            user=request.user,
            is_deleted=False
        )
        
        # Prepare recommendations as list
        recommendations = []
        if report.recommendations:
            recommendations = [r.strip() for r in report.recommendations.split('\n') if r.strip()]
        
        # Generate summary if not present (for old reports)
        summary = ""
        if hasattr(report, 'summary') and report.summary:
            summary = report.summary
        else:
            # Generate summary from existing data
            summary = f"""Your emotional state shows {report.overall_sentiment} sentiment with an average score of {report.average_score:.2f}.

Sentiment Distribution:
• Positive messages: {report.positive_count} ({report.positive_percentage:.1f}%)
• Neutral messages: {report.neutral_count} ({report.neutral_percentage:.1f}%)
• Negative messages: {report.negative_count} ({report.negative_percentage:.1f}%)

Out of {report.total_messages} messages analyzed during {report.start_date.strftime('%B %d')} to {report.end_date.strftime('%B %d, %Y')}, the analysis provides insights into your emotional patterns."""
        
        # Prepare emotion data
        dominant_emotions = report.dominant_emotions if report.dominant_emotions else {}
        
        # Build comprehensive report data
        report_data = {
            'id': report.id,
            'overall_sentiment': report.overall_sentiment,
            'average_score': round(report.average_score, 3),
            'total_messages': report.total_messages,
            'positive_count': report.positive_count,
            'negative_count': report.negative_count,
            'neutral_count': report.neutral_count,
            'positive_percentage': round(report.positive_percentage, 1),
            'negative_percentage': round(report.negative_percentage, 1),
            'neutral_percentage': round(report.neutral_percentage, 1),
            'dominant_emotions': dominant_emotions,
            'recommendations': recommendations,
            'summary': summary,
            'start_date': report.start_date.strftime('%Y-%m-%d'),
            'end_date': report.end_date.strftime('%Y-%m-%d'),
            'created_at': report.created_at.strftime('%Y-%m-%d %H:%M'),
            'date_range_display': f"{report.start_date.strftime('%B %d')} - {report.end_date.strftime('%B %d, %Y')}"
        }
        
        return JsonResponse({
            'success': True,
            'report': report_data
        })
        
    except Exception as e:
        logger.error(f"Get report detail error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def get_sentiment_trend(request):
    """Get sentiment trend"""
    try:
        days = int(request.GET.get('days', 30))
        generator = ReportGenerator()
        trend = generator.get_user_sentiment_trend(request.user, days=days)
        return JsonResponse({'success': True, 'trend': trend})
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
        
        UserActivity.objects.create(
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
    """Toggle quote favorite"""
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
        
        return JsonResponse({'success': True, 'messages': messages_data})
    except Exception as e:
        logger.error(f"Get chat history error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_conversations(request):
    """Get all non-deleted conversations"""
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
        
        return JsonResponse({'success': True, 'conversations': conversations_data})
    except Exception as e:
        logger.error(f"Get conversations error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def delete_conversation(request):
    """Soft delete conversation and associated reports"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id is required'}, status=400)
        
        conversation = get_object_or_404(Conversation, session_id=session_id, user=request.user)
        conversation.soft_delete()
        
        log_audit(
            request.user,
            'conversation_deleted',
            f'Conversation {session_id} and associated reports deleted',
            request,
            'deletion'
        )
        
        return JsonResponse({'success': True, 'message': 'Conversation deleted successfully'})
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def clear_conversation(request):
    """Clear conversation messages"""
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
        
        Message.objects.filter(conversation=conversation).delete()
        conversation.title = "New Conversation"
        conversation.save()
        
        return JsonResponse({'success': True, 'message': 'Conversation cleared successfully'})
    except Exception as e:
        logger.error(f"Clear conversation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def create_new_conversation(request):
    """Create new conversation"""
    try:
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
    """Check Groq API status"""
    try:
        status = groq_service.check_health()
        
        messages = []
        if status.get('available'):
            messages.append(f"✅ Groq API is ready")
            messages.append(f"📦 Model: {status.get('model')}")
        else:
            messages.append(f"❌ Groq API unavailable: {status.get('error')}")
        
        return JsonResponse({
            'success': True,
            'status': status,
            'messages': messages,
            'groq_ready': status.get('available', False)
        })
    except Exception as e:
        logger.error(f"Check LLM status error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'messages': ['❌ Error checking service status']
        }, status=500)