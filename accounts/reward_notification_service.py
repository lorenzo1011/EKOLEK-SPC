"""
Reward Notification Service for E-KOLEK System
Handles sending email notifications to users when new rewards are added
"""
import logging
import threading
from django.conf import settings

logger = logging.getLogger(__name__)


def get_all_users_with_email():
    """
    Get all approved users with email addresses
    
    Returns:
        QuerySet of Users with email addresses
    """
    from accounts.models import Users
    
    # Get all approved, active users who have email addresses
    users = Users.objects.filter(
        status='approved',
        is_active=True,
        email__isnull=False
    ).exclude(email='')
    
    return users


def send_emails_in_background(user_emails, reward_data):
    """
    Send emails via Django's email system (now uses SendGrid backend).
    This function is called from a background thread.
    
    Args:
        user_emails: List of email addresses
        reward_data: Dictionary with reward information
    """
    from django.core.mail import EmailMultiAlternatives
    
    success_count = 0
    failed_emails = []
    
    logger.info(f"Background reward email sending started for {len(user_emails)} users")
    
    # NOTE: Image removed from email - Gmail blocks external images anyway
    # Users can view the image in the mobile app or web dashboard
    
    # Generate email content with beautiful HTML design
    subject = f"🎁 E-KOLEK: New Reward Available - {reward_data['name']}"
    
    # Create plain text message (fallback)
    message = f"""
Hello,

Great news! A new reward is now available in the E-KOLEK system!

🎁 Reward: {reward_data['name']}
📦 Category: {reward_data['category']}
⭐ Points Required: {reward_data['points']} points
📋 Description: {reward_data['description']}
📊 Stock Available: {reward_data['stock']} items

Start collecting points today and claim this amazing reward!

Open the E-KOLEK app to view the reward and start earning points.

Best regards,
E-KOLEK Team
    """
    
    # Create beautiful HTML email
    html_message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Reward Available</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f3f4f6;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                        
                        <!-- Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #ec4899 0%, #d946ef 100%); padding: 40px 30px; text-align: center;">
                                <table role="presentation" style="margin: 0 auto 20px;">
                                    <tr>
                                        <td style="background-color: rgba(255, 255, 255, 0.2); width: 80px; height: 80px; border-radius: 50%; text-align: center; vertical-align: middle; line-height: 80px;">
                                            <span style="font-size: 48px; display: inline-block; vertical-align: middle; line-height: normal;">🎁</span>
                                        </td>
                                    </tr>
                                </table>
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">E-KOLEK</h1>
                                <p style="color: rgba(255, 255, 255, 0.95); margin: 10px 0 0 0; font-size: 16px;">New Reward Available!</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <!-- Announcement Banner -->
                                <div style="background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%); border-left: 4px solid #ec4899; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center;">
                                    <h2 style="color: #ec4899; margin: 0; font-size: 22px; font-weight: 600;">✨ New Reward Added</h2>
                                </div>
                                
                                <!-- Reward Name -->
                                <div style="text-align: center; margin-bottom: 30px;">
                                    <h3 style="color: #1f2937; margin: 0; font-size: 24px; font-weight: 700;">🎁 {reward_data['name']}</h3>
                                </div>
                                
                                <!-- Reward Details Card -->
                                <div style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 2px solid #ec4899;">
                                    
                                    <!-- Category -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">📦 CATEGORY</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #1f2937; font-size: 16px; font-weight: 600;">{reward_data['category']}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Points Required -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">⭐ POINTS REQUIRED</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #ec4899; font-size: 20px; font-weight: 700;">{reward_data['points']} points</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Stock Available -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">📊 STOCK AVAILABLE</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #10b981; font-size: 18px; font-weight: 700;">{reward_data['stock']} items</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Description -->
                                    <div style="margin-bottom: 0;">
                                        <p style="color: #6b7280; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">📋 DESCRIPTION</p>
                                        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0;">{reward_data['description']}</p>
                                    </div>
                                    
                                </div>
                                
                                <!-- Call to Action -->
                                <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 25px;">
                                    <p style="color: #1e40af; margin: 0 0 10px 0; font-size: 16px; font-weight: 600; line-height: 1.6;">
                                        🌟 Start earning points today!
                                    </p>
                                    <p style="color: #3b82f6; margin: 0; font-size: 14px; line-height: 1.6;">
                                        Open the E-KOLEK app to view this reward and start collecting points through waste segregation activities.
                                    </p>
                                </div>
                                
                                <!-- How to Earn Points -->
                                <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px;">
                                    <p style="color: #6b7280; margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">💡 How to Earn Points:</p>
                                    <ul style="color: #6b7280; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                        <li>Properly segregate your waste</li>
                                        <li>Dispose waste on collection days</li>
                                        <li>Complete educational quizzes</li>
                                        <li>Watch learning videos</li>
                                        <li>Refer family and friends</li>
                                        <li>Participate in community activities</li>
                                    </ul>
                                </div>
                                
                                <!-- Urgency Note -->
                                <div style="background-color: #fef3c7; border-left: 3px solid #f59e0b; padding: 15px; border-radius: 6px; margin-top: 20px;">
                                    <p style="color: #92400e; margin: 0; font-size: 14px;"><strong>⚡ Limited Stock:</strong> Only {reward_data['stock']} items available. Claim yours before they run out!</p>
                                </div>
                                
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="color: #333333; margin: 0 0 5px 0; font-size: 14px; font-weight: 600;">Best regards,</p>
                                <p style="color: #6366f1; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">E-KOLEK Team</p>
                                <p style="color: #9ca3af; margin: 0; font-size: 12px;">© 2025 E-KOLEK. Environmental Management System</p>
                                <p style="color: #9ca3af; margin: 5px 0 0 0; font-size: 12px;">Promoting Clean and Green Communities 🌍</p>
                            </td>
                        </tr>
                        
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
    
    # Send to all users
    for i, email in enumerate(user_emails, 1):
        if not email:
            continue
        
        try:
            # Create EmailMultiAlternatives for better control
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[email]
            )
            
            # Add HTML version
            msg.attach_alternative(html_message, "text/html")
            
            # NOTE: No longer attaching image as file - it's embedded as base64 data URL in HTML
            # This prevents Gmail from showing downloadable attachment at bottom
            
            # Send email
            msg.send(fail_silently=False)
            
            success_count += 1
            logger.info(f"Background reward email sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send background reward email to {email}: {str(e)}")
            failed_emails.append(email)
    
    logger.info(f"Background reward email sending completed | Success: {success_count}/{len(user_emails)}")


def send_new_reward_notification(reward):
    """
    Send email notifications to all users about a new reward
    
    Args:
        reward: Reward model instance
    
    Returns:
        dict: Result with success status and details
    """
    try:
        logger.info(f"=== REWARD NOTIFICATION SERVICE ===")
        logger.info(f"New Reward: {reward.name} | Points: {reward.points_required}")
        
        # Get all users with email
        users = get_all_users_with_email()
        user_emails = list(users.values_list('email', flat=True))
        
        logger.info(f"Found {len(user_emails)} users with email addresses")
        
        if not user_emails:
            warning_msg = "WARNING: No users with email addresses found"
            logger.warning("No users with email found")
            return {
                'success': True,
                'message': 'No users with email to notify',
                'recipients_count': 0,
                'warning': 'No users with email addresses'
            }
        
        # Prepare reward data
        reward_data = {
            'name': reward.name,
            'category': reward.category.name if reward.category else 'General',
            'points': reward.points_required,
            'description': reward.description,
            'stock': reward.stock,
            'image_url': reward.image_url_for_email if reward.image else None  # Use email-optimized URL
        }
        
        # Debug logging for image URL
        if reward.image:
            logger.info(f"Image debug | name: {reward.image.name} | web_url: {reward.image_url} | email_url: {reward.image_url_for_email}")
        else:
            logger.warning("No image attached to reward")
        
        # Send emails in BACKGROUND THREAD so reward save is not blocked
        logger.info("Starting background email thread")
        
        # Start background thread for email sending (NO image parameter)
        email_thread = threading.Thread(
            target=send_emails_in_background,
            args=(user_emails, reward_data),
            daemon=True  # Thread will not prevent program exit
        )
        email_thread.start()
        
        logger.info(f"Email thread started | {len(user_emails)} emails queued for background sending")
        
        return {
            'success': True,
            'message': f'Reward saved! Notifications are being sent to {len(user_emails)} users in the background',
            'recipients_count': len(user_emails),
            'async': True,
            'background_thread': True
        }
    
    except Exception as e:
        error_msg = f"Reward notification service error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send notifications'
        }
