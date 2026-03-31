"""
Dashboard and notification views.
"""

import base64
import logging
from datetime import datetime, timedelta
from io import BytesIO

import qrcode
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from accounts.models import Family, GarbageSchedule, Notification, Reward, Users

logger = logging.getLogger(__name__)


def home(request):
    """Home page with real-time statistics"""
    # Get active users count
    active_users = Users.objects.filter(is_active=True).count()
    
    # Get total points earned across all users
    total_points = Users.objects.aggregate(total=Sum('total_points'))['total'] or 0
    
    # Calculate app rating (you can implement actual rating system later)
    # For now, use a high rating based on user engagement
    app_rating = "4.9" if active_users > 500 else "4.8" if active_users > 100 else "4.7"
    
    context = {
        'active_users': active_users,
        'total_points': int(total_points),
        'app_rating': app_rating,
    }
    
    return render(request, 'home.html', context)


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'terms_of_service.html')


@login_required(login_url='login_page')
@ensure_csrf_cookie
def userdashboard(request):
    """Para User dashboard"""
    user = request.user
    schedules = GarbageSchedule.objects.filter(barangay=user.get_barangay()).order_by('day', 'start_time')
    
    # Get current day and tomorrow's day
    today = datetime.now().strftime('%A')  # e.g., 'Monday'
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A')
    
    # Add is_today and is_tomorrow flags to schedules
    enhanced_schedules = []
    for schedule in schedules:
        schedule.is_today = schedule.day == today
        schedule.is_tomorrow = schedule.day == tomorrow
        enhanced_schedules.append(schedule)
    
    # Sort schedules: today first, tomorrow second, then rest
    enhanced_schedules.sort(key=lambda x: (not x.is_today, not x.is_tomorrow, x.day, x.start_time))
    
    # ============================================================
    # PER-BARANGAY REWARDS FILTERING
    # Only show rewards available to user's barangay
    # Global rewards (no barangays assigned) are shown to all users
    # ============================================================
    rewards = Reward.get_available_for_user(user, include_inactive=False)
    
    # Get all notifications for the user (limited to 20 most recent)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    # Count unread notifications (not viewed)
    unread_count = Notification.objects.filter(user=request.user, viewed_at__isnull=True).count()

    # User Leaderboard: order users by total_points, limit to top 10
    # FIX: Use select_related to avoid N+1 query when accessing family
    user_leaderboard_qs = Users.objects.filter(
        status='approved',
        total_points__gt=0  # Only include users with points > 0
    ).select_related('family').order_by('-total_points')[:10]
    
    user_leaderboard = []
    for i, leaderboard_user in enumerate(user_leaderboard_qs):
        user_leaderboard.append({
            'rank': i + 1,
            'full_name': leaderboard_user.full_name,
            'points': leaderboard_user.total_points,
            'family_name': leaderboard_user.family.family_name if leaderboard_user.family else 'No Family',
            'is_current_user': leaderboard_user.id == request.user.id
        })

    # Barangay Leaderboard: sum ALL user points by barangay, limit to top 10
    # FIX: Directly aggregate user points instead of using cached family points
    # This ensures accurate real-time totals from the source of truth
    barangay_leaderboard_qs = (
        Users.objects.filter(
            status='approved',
            total_points__gt=0,
            family__status='approved',
            family__barangay__isnull=False  # Ensure barangay exists
        )
        .values('family__barangay__name')
        .annotate(points=Sum('total_points'))
        .filter(points__gt=0)  # Only include barangays with points > 0
        .order_by('-points')[:10]
    )
    
    barangay_leaderboard = []
    for i, entry in enumerate(barangay_leaderboard_qs):
        barangay_leaderboard.append({
            'rank': i + 1,
            'barangay_name': entry['family__barangay__name'],
            'points': entry['points']
        })

    # Individual leaderboard within user's family
    # FIX: Only query if user has a family to avoid unnecessary database hit
    if user.family:
        family_member_leaderboard = user.family.members.filter(is_active=True).order_by('-total_points')[:5]
    else:
        family_member_leaderboard = []

    # Referral statistics
    referred_users_count = Users.objects.filter(referred_by_code=user.referral_code, status='approved').count()
    referral_points_earned = referred_users_count * 10  # 10 points per referral
    
    # Profile-specific calculations
    # Calculate user's age if date_of_birth is set
    user_age = None
    if user.date_of_birth:
        today_date = datetime.now().date()
        # Calculate age correctly by checking if birthday has occurred this year
        age = today_date.year - user.date_of_birth.year
        # If birthday hasn't occurred yet this year, subtract 1
        if (today_date.month, today_date.day) < (user.date_of_birth.month, user.date_of_birth.day):
            age -= 1
        user_age = age
    
    # Calculate days since member (member_since_days)
    member_since_days = (datetime.now().date() - user.created_at.date()).days
    
    # Calculate user's rank within family
    user_family_rank = user.family.members.filter(
        total_points__gt=user.total_points,
        is_active=True
    ).count() + 1
    
    # Generate QR code for user profile
    qr_code_data = generate_user_qr_code(user)

    return render(request, 'userdashboard.html', {
        'rewards': rewards,
        'schedules': enhanced_schedules,
        'notifications': notifications,
        'unread_notifications_count': unread_count,
        'user_leaderboard': user_leaderboard,
        'barangay_leaderboard': barangay_leaderboard,
        'family_member_leaderboard': family_member_leaderboard,
        'user_family': user.family,
        'referred_users_count': referred_users_count,
        'referral_points_earned': referral_points_earned,
        # Profile-specific context
        'user_age': user_age,
        'member_since_days': member_since_days,
        'user_family_rank': user_family_rank,
        'qr_code_base64': qr_code_data,  # Base64 encoded QR code image
    })


@login_required
@csrf_protect
def mark_notifications_viewed(request):
    """
    API endpoint to mark notifications as viewed when user opens the notifications tab
    """
    if request.method == 'POST':
        try:
            # Mark all unviewed notifications for this user as viewed
            updated_count = Notification.objects.filter(
                user=request.user,
                viewed_at__isnull=True
            ).update(viewed_at=timezone.now())
            
            return JsonResponse({
                'success': True,
                'message': f'{updated_count} notifications marked as viewed',
                'updated_count': updated_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)


@login_required
def get_unread_count(request):
    """
    API endpoint to get the count of unread notifications
    """
    try:
        unread_count = Notification.objects.filter(
            user=request.user,
            viewed_at__isnull=True
        ).count()
        
        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def generate_user_qr_code(user):
    """
    Generate QR code for user containing their ID.
    Returns base64 encoded image that can be embedded directly in HTML.
    
    The QR code contains the user's UUID which admins scan during transactions.
    """
    try:
        # Create QR code with user's UUID
        qr = qrcode.QRCode(
            version=1,  # Size of QR code (1-40, 1 is smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
            box_size=10,  # Size of each box in pixels
            border=4,  # Border size in boxes
        )
        
        # Add user ID as data (UUID as string)
        qr_data = str(user.id)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="#10b981", back_color="white")  # Green theme matching E-KOLEK
        
        # Convert to base64 for embedding in HTML
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return img_base64
    except Exception as e:
        logger.error(f"Error generating QR code for user {user.id}: {e}")
        return None


@login_required
def download_qr_code(request):
    """
    Generate and download user's QR code as PNG file.
    Filename includes username for easy identification.
    """
    try:
        user = request.user
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(str(user.id))
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="#10b981", back_color="white")
        
        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Return as downloadable file
        response = HttpResponse(buffer, content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="ekolek_qr_{user.username}.png"'
        
        return response
    except Exception as e:
        logger.error(f"Error downloading QR code for user {user.id}: {e}")
        return HttpResponse("Error generating QR code", status=500)

