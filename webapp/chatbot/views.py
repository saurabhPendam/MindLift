from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import json
import uuid
import logging

from .models import (
    UserProfile, Conversation, Message, SentimentReport,
    Activity, UserActivity, MotivationalQuote, UserQuoteFavorite,
    DoctorAppointment, AuditLog, OTPVerification, AuthorizedEmail,
    PHQ9Assessment, GAD7Assessment, CBTThoughtRecord, CBTBehavioralActivation,
    CBTExposureHierarchy, InterventionOutcome, TheoreticalFramework
)
from .sentiment_service import SentimentAnalyzer, ReportGenerator
from .groq_service import groq_service
from .cbt_service import CBTService, AssessmentAnalytics, SDTFramework

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
    """User registration with authorized Gmail check"""
    if request.user.is_authenticated:
        return redirect('chat')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not first_name or not last_name or not username or not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'register.html')
        
        # Validate first and last names
        if len(first_name) < 2 or len(last_name) < 2:
            messages.error(request, 'First and last name must be at least 2 characters each')
            return render(request, 'register.html')
        
        # Strict Gmail validation to prevent fake/temp emails
        if not email.endswith('@gmail.com'):
            messages.error(request, 'For security reasons, only Gmail accounts (@gmail.com) are allowed to register. This helps us verify user authenticity and prevent fake accounts.')
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
            # Generate OTP for email verification
            otp_code = OTPVerification.generate_otp()
            
            # Store registration data in session temporarily
            request.session['registration_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'email': email,
                'password': password,
                'otp_code': otp_code,
                'otp_created': timezone.now().isoformat()
            }
            
            # Send verification email
            send_mail(
                subject='MindLift - Verify Your Email Address',
                message=f'Welcome to MindLift!\n\nYour email verification code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this registration, please ignore this email.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            # Log registration attempt
            log_audit(None, 'registration_started', 
                     f'Registration OTP sent to: {email}', 
                     request, 'account')
            
            messages.success(request, f'Verification code sent to {email}. Please check your email.')
            return redirect('verify_registration')
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, 'Failed to send verification email. Please check your email and try again.')
            return render(request, 'register.html')
    
    return render(request, 'register.html')


def verify_registration(request):
    """Verify email during registration"""
    registration_data = request.session.get('registration_data')
    
    if not registration_data:
        messages.error(request, 'Registration session expired. Please register again.')
        return redirect('register')
    
    # Check if OTP expired (10 minutes)
    otp_created = timezone.datetime.fromisoformat(registration_data['otp_created'])
    if timezone.now() > otp_created + timedelta(minutes=10):
        request.session.pop('registration_data', None)
        messages.error(request, 'Verification code expired. Please register again.')
        return redirect('register')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the verification code')
            return render(request, 'verify_registration.html', {
                'email': registration_data['email']
            })
        
        # Verify OTP
        if otp_code == registration_data['otp_code']:
            try:
                # Create user account
                user = User.objects.create_user(
                    username=registration_data['username'],
                    email=registration_data['email'],
                    password=registration_data['password'],
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name']
                )
                
                # Create user profile
                UserProfile.objects.create(
                    user=user,
                    two_factor_enabled=True,
                    is_authorized_email=True  # Email verified during registration
                )
                
                # Clear registration data
                request.session.pop('registration_data', None)
                
                # Log successful registration
                log_audit(user, 'account_created', 
                         f'Email verified and account created: {user.username}', 
                         request, 'account')
                
                # Auto-login
                login(request, user)
                display_name = f"{user.first_name} {user.last_name}".strip()
                messages.success(request, f'Welcome to MindLift, {display_name}! Your account has been verified.')
                return redirect('chat')
                
            except Exception as e:
                logger.error(f"Account creation error: {str(e)}")
                messages.error(request, 'Failed to create account. Please try again.')
                request.session.pop('registration_data', None)
                return redirect('register')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
            log_audit(None, 'failed_registration_otp', 
                     f'Failed registration OTP for: {registration_data["email"]}', 
                     request, 'security')
            return render(request, 'verify_registration.html', {
                'email': registration_data['email']
            })
    
    return render(request, 'verify_registration.html', {
        'email': registration_data['email']
    })


def resend_registration_otp(request):
    """Resend registration verification OTP"""
    registration_data = request.session.get('registration_data')
    
    if not registration_data:
        return JsonResponse({'success': False, 'message': 'Session expired'})
    
    try:
        # Generate new OTP
        otp_code = OTPVerification.generate_otp()
        
        # Update session with new OTP
        registration_data['otp_code'] = otp_code
        registration_data['otp_created'] = timezone.now().isoformat()
        request.session['registration_data'] = registration_data
        
        # Send new verification email
        send_mail(
            subject='MindLift - New Verification Code',
            message=f'Your new email verification code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration_data['email']],
            fail_silently=False,
        )
        
        log_audit(None, 'registration_otp_resent', 
                 f'Registration OTP resent to: {registration_data["email"]}', 
                 request, 'security')
        return JsonResponse({'success': True, 'message': 'New verification code sent to your email'})
        
    except Exception as e:
        logger.error(f'Failed to resend registration OTP: {str(e)}')
        return JsonResponse({'success': False, 'message': 'Failed to send verification code'})


def login_view(request):
    """User login with 2FA OTP verification"""
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
            # Check if user profile exists
            try:
                profile = user.profile
                # Optional: Check if specifically flagged accounts need authorization
                # Removed strict authorization check to allow normal login
                if False:  # Disabled authorization check for normal users
                    messages.error(request, 'Your account is not authorized to access this system.')
                    log_audit(user, 'unauthorized_login', 
                             f'Unauthorized login attempt: {username}', 
                             request, 'security')
                    return render(request, 'login.html')
                
                # Check if account deletion is pending
                if profile.deletion_requested:
                    messages.warning(request, 
                        f'Your account deletion is scheduled for {profile.deletion_scheduled_for.strftime("%Y-%m-%d")}. '
                        'You can cancel it from your profile settings.')
            except UserProfile.DoesNotExist:
                # Create profile if doesn't exist
                profile = UserProfile.objects.create(
                    user=user,
                    is_authorized_email=False  # Set to False by default, can be updated later
                )
            
            # Check if 2FA is enabled
            if profile.two_factor_enabled:
                # Generate and send OTP
                otp_code = OTPVerification.generate_otp()
                expires_at = timezone.now() + timedelta(minutes=10)
                
                OTPVerification.objects.create(
                    user=user,
                    otp_code=otp_code,
                    expires_at=expires_at
                )
                
                # Send OTP via email
                try:
                    send_mail(
                        subject='MindLift - Your Login OTP Code',
                        message=f'Your OTP code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this code, please ignore this email.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    
                    # Store user ID in session for OTP verification
                    request.session['otp_user_id'] = user.id
                    request.session['otp_username'] = username
                    
                    log_audit(user, 'otp_sent', f'OTP sent to {user.email}', request, 'security')
                    messages.success(request, f'OTP has been sent to {user.email}. Please check your email.')
                    return redirect('verify_otp')
                    
                except Exception as e:
                    logger.error(f'Failed to send OTP email: {str(e)}')
                    messages.error(request, 'Failed to send OTP. Please try again later.')
                    return render(request, 'login.html')
            else:
                # Login without 2FA
                login(request, user)
                log_audit(user, 'login', f'User logged in: {username}', request, 'security')
                display_name = f"{user.first_name} {user.last_name}".strip() or username
                messages.success(request, f'Welcome back, {display_name}!')
                return redirect('chat')
        else:
            log_audit(None, 'failed_login', f'Failed login attempt for username: {username}', request, 'security')
            messages.error(request, 'Invalid username or password')
            return render(request, 'login.html')
    
    return render(request, 'login.html')


def verify_otp(request):
    """Verify OTP for 2FA"""
    # Check if user is in OTP verification process
    user_id = request.session.get('otp_user_id')
    username = request.session.get('otp_username')
    
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Invalid session. Please login again.')
        return redirect('login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP code')
            return render(request, 'verify_otp.html', {'username': username})
        
        # Get the latest valid OTP for this user
        try:
            otp = OTPVerification.objects.filter(
                user=user,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp:
                messages.error(request, 'No valid OTP found. Please request a new one.')
                return redirect('login')
            
            if otp.verify(otp_code):
                # OTP verified successfully
                login(request, user)
                
                # Clear session data
                request.session.pop('otp_user_id', None)
                request.session.pop('otp_username', None)
                
                log_audit(user, 'login_2fa_success', f'User logged in with 2FA: {username}', request, 'security')
                messages.success(request, f'Welcome back, {username}!')
                return redirect('chat')
            else:
                if not otp.is_valid():
                    messages.error(request, 'OTP has expired or maximum attempts exceeded. Please login again.')
                    return redirect('login')
                else:
                    messages.error(request, f'Invalid OTP code. {5 - otp.attempt_count} attempts remaining.')
                    log_audit(user, 'failed_otp', f'Failed OTP attempt for {username}', request, 'security')
                    return render(request, 'verify_otp.html', {'username': username})
                    
        except Exception as e:
            logger.error(f'OTP verification error: {str(e)}')
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'verify_otp.html', {'username': username})
    
    return render(request, 'verify_otp.html', {'username': username})


def resend_otp(request):
    """Resend OTP code"""
    user_id = request.session.get('otp_user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'message': 'Session expired'})
    
    try:
        user = User.objects.get(id=user_id)
        
        # Invalidate old OTPs
        OTPVerification.objects.filter(
            user=user,
            is_used=False
        ).update(is_used=True)
        
        # Generate new OTP
        otp_code = OTPVerification.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)
        
        OTPVerification.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        # Send OTP via email
        send_mail(
            subject='MindLift - Your New Login OTP Code',
            message=f'Your new OTP code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this code, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        log_audit(user, 'otp_resent', f'OTP resent to {user.email}', request, 'security')
        return JsonResponse({'success': True, 'message': 'New OTP sent to your email'})
        
    except Exception as e:
        logger.error(f'Failed to resend OTP: {str(e)}')
        return JsonResponse({'success': False, 'message': 'Failed to send OTP'})


def logout_view(request):
    """Redirect to feedback page before logout"""
    if request.user.is_authenticated:
        log_audit(request.user, 'logout_initiated', f'User initiated logout: {request.user.username}', request, 'security')
        return redirect('feedback')
    return redirect('home')


@require_http_methods(["GET"])
def complete_logout(request):
    """Complete logout without feedback"""
    if request.user.is_authenticated:
        log_audit(request.user, 'logout', f'User logged out: {request.user.username}', request, 'security')
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('home')


def feedback_page(request):
    """Display feedback page"""
    return render(request, 'feedback.html')


@require_http_methods(["POST"])
def submit_feedback(request):
    """Submit user feedback"""
    try:
        rating = request.POST.get('rating')
        category = request.POST.get('category')
        message = request.POST.get('message')
        email = request.POST.get('email', '').strip()
        would_recommend = request.POST.get('would_recommend', '')
        
        if not rating or not category or not message:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        from .models import Feedback
        
        feedback = Feedback.objects.create(
            user=request.user if request.user.is_authenticated else None,
            rating=int(rating),
            category=category,
            message=message,
            email=email if email else None,
            would_recommend=would_recommend if would_recommend else None
        )
        
        logger.info(f"Feedback submitted: {feedback.id} - Rating: {rating} - Category: {category}")
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'Failed to submit feedback'}, status=500)


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
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
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
        'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
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
@require_http_methods(["POST"])
def update_profile(request):
    """Update user profile information"""
    try:
        data = json.loads(request.body)
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        new_password = data.get('new_password', '').strip()
        
        user = request.user
        
        # Update name if provided
        if first_name and len(first_name) >= 2:
            user.first_name = first_name
        
        if last_name and len(last_name) >= 2:
            user.last_name = last_name
        
        # Update email if provided and different
        if email and email != user.email:
            # Check if email is already taken
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return JsonResponse({'error': 'Email already in use'}, status=400)
            
            # Validate Gmail only
            if not email.endswith('@gmail.com'):
                return JsonResponse({'error': 'Only Gmail accounts are allowed'}, status=400)
            
            user.email = email
        
        # Update password if provided
        if new_password and len(new_password) >= 6:
            user.set_password(new_password)
        
        user.save()
        
        log_audit(
            user,
            'profile_updated',
            'User updated profile information',
            request,
            'account'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully',
            'full_name': f"{user.first_name} {user.last_name}".strip()
        })
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


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
        
        # === HYBRID SYSTEM: Use RASA + Groq + ECFN ===
        from .hybrid_service import hybrid_service
        
        # Initialize variables to avoid UnboundLocalError
        intent = None
        confidence = None
        ecfn_data = None
        
        try:
            logger.info("🚀 Processing message through Hybrid System with ECFN")
            
            # Process through hybrid system with ECFN enabled
            bot_response = hybrid_service.process_message(
                message=user_message,
                user_id=str(request.user.id),
                context=context,
                user=request.user,  # Pass user for ECFN analysis
                enable_ecfn=True  # Enable advanced emotion-context fusion
            )
            
            if not bot_response or not bot_response.get('success'):
                raise Exception("Hybrid system returned unsuccessful response")
            
            # Extract response components
            bot_text = bot_response.get('text', '')
            video_info = bot_response.get('video')
            response_source = bot_response.get('source', 'unknown')
            intent = bot_response.get('intent')
            confidence = bot_response.get('confidence')
            ecfn_data = bot_response.get('ecfn')  # ECFN analysis results
            
            # Log which system was used
            logger.info(f"✅ Response from: {response_source}")
            if intent:
                logger.info(f"📊 Intent: {intent} (confidence: {confidence:.2f})")
            if ecfn_data:
                logger.info(f"🧠 ECFN: Emotion={ecfn_data.get('emotion')}, Trend={ecfn_data.get('mood_trend')}, Risk={ecfn_data.get('crisis_risk')}")
            
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


# ============================================
# CLINICAL ASSESSMENT VIEWS (PHQ-9, GAD-7)
# ============================================

@login_required
@require_http_methods(["GET", "POST"])
def phq9_assessment(request):
    """PHQ-9 Depression Assessment"""
    if request.method == 'GET':
        # Get user's assessment history
        assessments = PHQ9Assessment.objects.filter(user=request.user).order_by('-completed_at')[:10]
        return render(request, 'assessments/phq9.html', {
            'assessments': assessments
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            responses = data.get('responses', [])
            
            # Validate responses
            if len(responses) != 9:
                return JsonResponse({'success': False, 'error': 'Invalid number of responses'}, status=400)
            
            # Calculate score and severity before creating the object
            total_score = sum(responses)
            
            # Determine severity
            if total_score <= 4:
                severity = 'minimal'
            elif total_score <= 9:
                severity = 'mild'
            elif total_score <= 14:
                severity = 'moderate'
            elif total_score <= 19:
                severity = 'moderately_severe'
            else:
                severity = 'severe'
            
            # Flag for intervention if moderate or higher, or suicidal ideation present
            requires_intervention = (total_score >= 10 or responses[8] >= 1)
            
            # Create PHQ-9 assessment with calculated values
            assessment = PHQ9Assessment.objects.create(
                user=request.user,
                assessment_type=data.get('assessment_type', 'baseline'),
                q1_interest=responses[0],
                q2_depressed=responses[1],
                q3_sleep=responses[2],
                q4_fatigue=responses[3],
                q5_appetite=responses[4],
                q6_failure=responses[5],
                q7_concentration=responses[6],
                q8_psychomotor=responses[7],
                q9_suicidal=responses[8],
                total_score=total_score,
                severity=severity,
                requires_intervention=requires_intervention
            )
            
            # Log the assessment
            log_audit(
                request.user,
                'PHQ-9 Assessment Completed',
                f'Score: {assessment.total_score}, Severity: {assessment.severity}',
                request,
                category='assessment'
            )
            
            # Check for crisis
            if assessment.q9_suicidal >= 1:
                log_audit(
                    request.user,
                    'Suicidal Ideation Detected',
                    f'PHQ-9 Question 9 score: {assessment.q9_suicidal}',
                    request,
                    category='crisis'
                )
            
            return JsonResponse({
                'success': True,
                'assessment': {
                    'id': assessment.id,
                    'total_score': assessment.total_score,
                    'severity': assessment.severity,
                    'severity_display': assessment.get_severity_display(),
                    'requires_intervention': assessment.requires_intervention
                },
                'message': f'PHQ-9 completed. Score: {assessment.total_score} ({assessment.get_severity_display()})'
            })
        
        except Exception as e:
            logger.error(f"PHQ-9 assessment error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def gad7_assessment(request):
    """GAD-7 Anxiety Assessment"""
    if request.method == 'GET':
        # Get user's assessment history
        assessments = GAD7Assessment.objects.filter(user=request.user).order_by('-completed_at')[:10]
        return render(request, 'assessments/gad7.html', {
            'assessments': assessments
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            responses = data.get('responses', [])
            
            # Validate responses
            if len(responses) != 7:
                return JsonResponse({'success': False, 'error': 'Invalid number of responses'}, status=400)
            
            # Calculate score and severity before creating the object
            total_score = sum(responses)
            
            # Determine severity
            if total_score <= 4:
                severity = 'minimal'
            elif total_score <= 9:
                severity = 'mild'
            elif total_score <= 14:
                severity = 'moderate'
            else:
                severity = 'severe'
            
            # Flag for intervention if moderate or higher
            requires_intervention = (total_score >= 10)
            
            # Create GAD-7 assessment with calculated values
            assessment = GAD7Assessment.objects.create(
                user=request.user,
                assessment_type=data.get('assessment_type', 'baseline'),
                q1_nervous=responses[0],
                q2_control=responses[1],
                q3_worrying=responses[2],
                q4_relaxing=responses[3],
                q5_restless=responses[4],
                q6_irritable=responses[5],
                q7_afraid=responses[6],
                total_score=total_score,
                severity=severity,
                requires_intervention=requires_intervention
            )
            
            # Log the assessment
            log_audit(
                request.user,
                'GAD-7 Assessment Completed',
                f'Score: {assessment.total_score}, Severity: {assessment.severity}',
                request,
                category='assessment'
            )
            
            return JsonResponse({
                'success': True,
                'assessment': {
                    'id': assessment.id,
                    'total_score': assessment.total_score,
                    'severity': assessment.severity,
                    'severity_display': assessment.get_severity_display(),
                    'requires_intervention': assessment.requires_intervention
                },
                'message': f'GAD-7 completed. Score: {assessment.total_score} ({assessment.get_severity_display()})'
            })
        
        except Exception as e:
            logger.error(f"GAD-7 assessment error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def assessment_progress(request):
    """View assessment progress and analytics"""
    try:
        # Generate comprehensive progress report
        progress_report = AssessmentAnalytics.generate_progress_report(request.user)
        
        # Get recent assessments
        recent_phq9 = PHQ9Assessment.objects.filter(user=request.user).order_by('-completed_at')[:5]
        recent_gad7 = GAD7Assessment.objects.filter(user=request.user).order_by('-completed_at')[:5]
        
        # Get CBT activities
        thought_records = CBTThoughtRecord.objects.filter(user=request.user).order_by('-created_at')[:5]
        behavioral_activities = CBTBehavioralActivation.objects.filter(user=request.user).order_by('-scheduled_date')[:5]
        
        return render(request, 'assessments/progress.html', {
            'progress_report': progress_report,
            'recent_phq9': recent_phq9,
            'recent_gad7': recent_gad7,
            'thought_records': thought_records,
            'behavioral_activities': behavioral_activities
        })
    
    except Exception as e:
        logger.error(f"Assessment progress error: {str(e)}")
        messages.error(request, 'Error loading progress data')
        return redirect('chat')


@login_required
@require_http_methods(["GET"])
def get_assessment_progress_api(request):
    """API endpoint for assessment progress data"""
    try:
        # Get PHQ-9 history
        phq9_assessments = PHQ9Assessment.objects.filter(user=request.user).order_by('completed_at')
        phq9_history = [
            {
                'date': assessment.completed_at.isoformat(),
                'score': assessment.total_score,
                'severity': assessment.severity,
                'severity_display': assessment.get_severity_display()
            }
            for assessment in phq9_assessments
        ]
        
        # Get GAD-7 history
        gad7_assessments = GAD7Assessment.objects.filter(user=request.user).order_by('completed_at')
        gad7_history = [
            {
                'date': assessment.completed_at.isoformat(),
                'score': assessment.total_score,
                'severity': assessment.severity,
                'severity_display': assessment.get_severity_display()
            }
            for assessment in gad7_assessments
        ]
        
        # Generate insights
        insights = []
        
        # PHQ-9 insights
        if len(phq9_assessments) >= 2:
            latest_phq9 = phq9_assessments.last()
            first_phq9 = phq9_assessments.first()
            change = first_phq9.total_score - latest_phq9.total_score
            
            if change > 0:
                insights.append({
                    'type': 'positive',
                    'message': f'Your PHQ-9 score has improved by {change} points since your first assessment!'
                })
            elif change < 0:
                insights.append({
                    'type': 'warning',
                    'message': f'Your PHQ-9 score has increased by {abs(change)} points. Consider reaching out for support.'
                })
        
        # GAD-7 insights
        if len(gad7_assessments) >= 2:
            latest_gad7 = gad7_assessments.last()
            first_gad7 = gad7_assessments.first()
            change = first_gad7.total_score - latest_gad7.total_score
            
            if change > 0:
                insights.append({
                    'type': 'positive',
                    'message': f'Your GAD-7 score has improved by {change} points since your first assessment!'
                })
            elif change < 0:
                insights.append({
                    'type': 'warning',
                    'message': f'Your GAD-7 score has increased by {abs(change)} points. Consider professional support.'
                })
        
        return JsonResponse({
            'success': True,
            'phq9_history': phq9_history,
            'gad7_history': gad7_history,
            'insights': insights
        })
    
    except Exception as e:
        logger.error(f"Assessment progress API error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# CBT INTERVENTION VIEWS
# ============================================

@login_required
@require_http_methods(["GET", "POST"])
def cbt_thought_record(request):
    """Create and view CBT thought records"""
    if request.method == 'GET':
        records = CBTThoughtRecord.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'cbt/thought_records.html', {'records': records})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            record = CBTThoughtRecord.objects.create(
                user=request.user,
                situation=data['situation'],
                automatic_thoughts=data['automatic_thoughts'],
                emotions=data.get('emotions', {}),
                evidence_for=data.get('evidence_for', ''),
                evidence_against=data.get('evidence_against', ''),
                alternative_thought=data.get('alternative_thought', ''),
                emotions_after=data.get('emotions_after', {}),
                completed=data.get('completed', False)
            )
            
            # Identify cognitive distortions
            distortions = CBTService.identify_distortions(data['automatic_thoughts'])
            record.distortions = distortions
            record.save()
            
            # Generate Socratic questions
            questions = []
            for distortion in distortions:
                questions.extend(CBTService.generate_socratic_questions(distortion))
            
            return JsonResponse({
                'success': True,
                'record_id': record.id,
                'distortions': [CBTService.COGNITIVE_DISTORTIONS.get(d, d) for d in distortions],
                'socratic_questions': questions[:3],  # Top 3 questions
                'message': 'Thought record created successfully'
            })
        
        except Exception as e:
            logger.error(f"Thought record error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def cbt_behavioral_activation(request):
    """Create behavioral activation plan"""
    try:
        data = json.loads(request.body)
        
        activity = CBTBehavioralActivation.objects.create(
            user=request.user,
            activity_name=data['activity_name'],
            activity_description=data.get('activity_description', ''),
            activity_type=data['activity_type'],
            scheduled_date=data['scheduled_date'],
            scheduled_time=data.get('scheduled_time'),
            duration_minutes=data.get('duration_minutes', 30),
            predicted_pleasure=data['predicted_pleasure'],
            predicted_mastery=data['predicted_mastery'],
            autonomy_support=data.get('autonomy_support', True),
            competence_building=data.get('competence_building', False),
            relatedness_fostering=data.get('relatedness_fostering', False)
        )
        
        return JsonResponse({
            'success': True,
            'activity_id': activity.id,
            'message': 'Activity scheduled successfully'
        })
    
    except Exception as e:
        logger.error(f"Behavioral activation error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def complete_behavioral_activation(request, activity_id):
    """Mark behavioral activation as complete and record outcomes"""
    try:
        activity = get_object_or_404(CBTBehavioralActivation, id=activity_id, user=request.user)
        data = json.loads(request.body)
        
        activity.completed = True
        activity.completed_at = timezone.now()
        activity.actual_pleasure = data['actual_pleasure']
        activity.actual_mastery = data['actual_mastery']
        activity.completion_notes = data.get('completion_notes', '')
        activity.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Activity completed! Great job!',
            'sdt_feedback': SDTFramework.build_competence_feedback(
                success_rate=0.7,  # Could calculate from user history
                difficulty='medium'
            )
        })
    
    except Exception as e:
        logger.error(f"Complete activity error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_cbt_suggestions(request):
    """Get personalized CBT suggestions based on assessment scores"""
    try:
        # Get latest assessments
        latest_phq9 = PHQ9Assessment.objects.filter(user=request.user).order_by('-completed_at').first()
        latest_gad7 = GAD7Assessment.objects.filter(user=request.user).order_by('-completed_at').first()
        
        suggestions = {
            'thought_records': False,
            'behavioral_activation': False,
            'exposure_therapy': False,
            'recommendations': []
        }
        
        # Depression-focused interventions
        if latest_phq9 and latest_phq9.total_score >= 10:
            suggestions['behavioral_activation'] = True
            suggestions['recommendations'].append({
                'type': 'behavioral_activation',
                'title': 'Behavioral Activation',
                'description': 'Schedule pleasant activities to combat depression',
                'priority': 'high'
            })
        
        # Anxiety-focused interventions
        if latest_gad7 and latest_gad7.total_score >= 10:
            suggestions['exposure_therapy'] = True
            suggestions['recommendations'].append({
                'type': 'exposure',
                'title': 'Gradual Exposure',
                'description': 'Face your fears step-by-step in a controlled way',
                'priority': 'high'
            })
        
        # Thought records useful for both
        if (latest_phq9 and latest_phq9.total_score >= 5) or (latest_gad7 and latest_gad7.total_score >= 5):
            suggestions['thought_records'] = True
            suggestions['recommendations'].append({
                'type': 'thought_record',
                'title': 'Thought Records',
                'description': 'Challenge negative thinking patterns',
                'priority': 'medium'
            })
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"CBT suggestions error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)