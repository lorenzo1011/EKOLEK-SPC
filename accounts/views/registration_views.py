"""
User registration views (family and member registration)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from datetime import date
import logging

from accounts.models import Barangay, Users
from cenro.models import TermsAndConditions
from accounts.models import UserConsent
from accounts.forms import FamilyRegistrationForm, FamilyMemberRegistrationForm

logger = logging.getLogger(__name__)

# ==============================================================================
# PER-FEATURE OTP FLAGS FOR REGISTRATION
# ==============================================================================
# Registration now NEVER requires OTP (cleaner UX, faster onboarding)
# This prevents 500 errors from missing OTP session variables
OTP_REGISTER_ENABLED = getattr(settings, 'OTP_REGISTER_ENABLED', False)
OTP_RESET_PASSWORD_ENABLED = getattr(settings, 'OTP_RESET_PASSWORD_ENABLED', True)

# Legacy flag (kept for backward compatibility)
OTP_VERIFICATION_ENABLED = getattr(settings, 'OTP_VERIFICATION_ENABLED', True)


def register(request):
    """Show registration selection page"""
    return render(request, 'register_select.html')


def register_family(request):
    """
    Family registration - Creates a new family and family representative.
    
    IMPORTANT FIX: OTP is now DISABLED for registration
    - Old behavior: Require phone and email OTP verification before registration
    - New behavior: Direct registration without OTP (faster onboarding, no errors)
    - This eliminates 500 errors from missing OTP session variables
    """
    if request.method == 'POST':
        form = FamilyRegistrationForm(request.POST)
        
        # ============================================================
        # FIX: Registration now NEVER requires OTP
        # OTP_REGISTER_ENABLED is set to False in settings
        # This provides cleaner UX and prevents 500 errors
        # ============================================================
        if not OTP_REGISTER_ENABLED:
            logger.info("[REGISTRATION] OTP disabled - proceeding with direct registration")
            
            if form.is_valid():
                # Check terms acceptance
                if not form.cleaned_data.get('accept_terms'):
                    messages.error(request, "You must accept the Terms and Conditions to register.")
                    barangays = Barangay.objects.all()
                    return render(request, 'register.html', {
                        'form': form,
                        'barangays': barangays,
                        'registration_type': 'family',
                        'today': date.today()
                    })
                
                # Direct registration without OTP
                family = form.save()
                
                # Get the representative user (the one with is_family_representative=True)
                representative = family.members.filter(is_family_representative=True).first()
                
                # Create consent records for both English and Tagalog terms
                if representative:
                    try:
                        english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                        tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                        
                        if english_terms:
                            UserConsent.create_consent(representative, english_terms, request)
                        if tagalog_terms:
                            UserConsent.create_consent(representative, tagalog_terms, request)
                    except Exception as e:
                        logger.error(f"Error creating user consent: {e}")
                
                logger.info(f"[REGISTRATION] Family {family.family_name} registered successfully (no OTP)")
                
                # Use Django messages with 'registration' tag for special styling
                success_msg = (
                    "✅ Registration Successful! "
                    "<div class='message-info'>"
                    "⏳ <strong>Waiting for Admin Approval</strong><br>"
                    "📱 You will receive an SMS notification once your account is approved. "
                    "Please wait for administrator approval before attempting to log in."
                    "</div>"
                )
                messages.success(request, success_msg, extra_tags='registration')
                
                return redirect('login_page')
        else:
            # OTP registration path (only used if OTP_REGISTER_ENABLED=True)
            # This code is kept for flexibility but not recommended
            logger.info("[REGISTRATION] OTP enabled - checking OTP verification")
            
            # Check if OTP has been verified for both phone and email
            otp_verified = request.POST.get('otp_verified') == 'true'
            verified_phone = request.session.get('verified_phone')
            form_phone = request.POST.get('phone')
            
            email_otp_verified = request.POST.get('email_otp_verified') == 'true'
            verified_email = request.session.get('verified_email')
            form_email = request.POST.get('email')
            
            if not otp_verified or verified_phone != form_phone:
                messages.error(request, "Please verify your phone number first.")
                barangays = Barangay.objects.all()
                return render(request, 'register.html', {
                    'form': form,
                    'barangays': barangays,
                    'registration_type': 'family',
                    'today': date.today(),
                    'otp_enabled': OTP_REGISTER_ENABLED
                })
            
            if not email_otp_verified or verified_email != form_email:
                messages.error(request, "Please verify your email address first.")
                barangays = Barangay.objects.all()
                return render(request, 'register.html', {
                    'form': form,
                    'barangays': barangays,
                    'registration_type': 'family',
                    'today': date.today(),
                    'otp_enabled': OTP_REGISTER_ENABLED
                })
            
            if form.is_valid():
                # Check terms acceptance
                if not form.cleaned_data.get('accept_terms'):
                    messages.error(request, "You must accept the Terms and Conditions to register.")
                    barangays = Barangay.objects.all()
                    return render(request, 'register.html', {
                        'form': form,
                        'barangays': barangays,
                        'registration_type': 'family',
                        'today': date.today(),
                        'otp_enabled': OTP_REGISTER_ENABLED
                    })
                
                # Both OTP verified, proceed with registration
                family = form.save()
                
                # Get the representative user (the one with is_family_representative=True)
                representative = family.members.filter(is_family_representative=True).first()
                
                # Create consent records for both English and Tagalog terms
                if representative:
                    try:
                        english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                        tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                        
                        if english_terms:
                            UserConsent.create_consent(representative, english_terms, request)
                        if tagalog_terms:
                            UserConsent.create_consent(representative, tagalog_terms, request)
                    except Exception as e:
                        logger.error(f"Error creating user consent: {e}")
                
                # Clear OTP session data
                request.session.pop('otp_verified', None)
                request.session.pop('verified_phone', None)
                request.session.pop('email_otp_verified', None)
                request.session.pop('verified_email', None)
            
            # Show success message with registration tag
            success_msg = (
                "✅ Registration Successful! "
                "<div class='message-info'>"
                "⏳ <strong>Waiting for Admin Approval</strong><br>"
                "📱 You will receive an SMS notification once your account is approved. "
                "Please wait for administrator approval before attempting to log in."
                "</div>"
            )
            messages.success(request, success_msg, extra_tags='registration')
            
            return redirect('login_page')
    else:
        form = FamilyRegistrationForm()

    # Get all barangays for the dropdown
    barangays = Barangay.objects.all()
    
    return render(request, 'register.html', {
        'form': form,
        'barangays': barangays,
        'registration_type': 'family',
        'today': date.today(),
        'otp_enabled': OTP_VERIFICATION_ENABLED
    })


def register_member(request):
    """Para sa family member registration (join existing family)"""
    if request.method == 'POST':
        form = FamilyMemberRegistrationForm(request.POST)
        
        # Check if OTP verification is disabled - if so, skip OTP checks
        if not OTP_VERIFICATION_ENABLED:
            logger.info("[OTP BYPASS] OTP verification disabled - skipping OTP checks for member registration")
            
            if form.is_valid():
                # Check terms acceptance
                if not form.cleaned_data.get('accept_terms'):
                    messages.error(request, "You must accept the Terms and Conditions to register.")
                    return render(request, 'register_member.html', {
                        'form': form,
                        'registration_type': 'member',
                        'today': date.today(),
                        'otp_enabled': OTP_VERIFICATION_ENABLED
                    })
                
                # OTP bypassed, proceed with registration
                user = form.save()
                
                # Create consent records for both English and Tagalog terms
                try:
                    english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                    tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                    
                    if english_terms:
                        UserConsent.create_consent(user, english_terms, request)
                    if tagalog_terms:
                        UserConsent.create_consent(user, tagalog_terms, request)
                except Exception as e:
                    logger.error(f"Error creating user consent: {e}")
                
                # Show success message with registration tag
                success_msg = (
                    "✅ Registration Successful! "
                    "<div class='message-info'>"
                    "⏳ <strong>Waiting for Admin Approval</strong><br>"
                    "📱 You will receive an SMS notification once your account is approved. "
                    "Please wait for administrator approval before attempting to log in."
                    "</div>"
                )
                messages.success(request, success_msg, extra_tags='registration')
                
                return redirect('login_page')
        
        # OTP is enabled - check OTP verification
        # Check if OTP has been verified for both phone and email
        otp_verified = request.POST.get('otp_verified') == 'true'
        verified_phone = request.session.get('verified_phone')
        form_phone = request.POST.get('phone')
        
        email_otp_verified = request.POST.get('email_otp_verified') == 'true'
        verified_email = request.session.get('verified_email')
        form_email = request.POST.get('email')
        
        if not otp_verified or verified_phone != form_phone:
            messages.error(request, "Please verify your phone number first.")
            return render(request, 'register_member.html', {
                'form': form,
                'registration_type': 'member',
                'today': date.today(),
                'otp_enabled': OTP_VERIFICATION_ENABLED
            })
        
        if not email_otp_verified or verified_email != form_email:
            messages.error(request, "Please verify your email address first.")
            return render(request, 'register_member.html', {
                'form': form,
                'registration_type': 'member',
                'today': date.today(),
                'otp_enabled': OTP_VERIFICATION_ENABLED
            })
        
        if form.is_valid():
            # Check terms acceptance
            if not form.cleaned_data.get('accept_terms'):
                messages.error(request, "You must accept the Terms and Conditions to register.")
                return render(request, 'register_member.html', {
                    'form': form,
                    'registration_type': 'member',
                    'today': date.today(),
                    'otp_enabled': OTP_VERIFICATION_ENABLED
                })
            
            # Both OTP verified, proceed with registration
            user = form.save()
            
            # Create consent records for both English and Tagalog terms
            try:
                english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                
                if english_terms:
                    UserConsent.create_consent(user, english_terms, request)
                if tagalog_terms:
                    UserConsent.create_consent(user, tagalog_terms, request)
            except Exception as e:
                logger.error(f"Error creating user consent: {e}")
            
            # Clear OTP session data
            request.session.pop('otp_verified', None)
            request.session.pop('verified_phone', None)
            request.session.pop('email_otp_verified', None)
            request.session.pop('verified_email', None)
            
            # Show success message with registration tag
            success_msg = (
                "✅ Registration Successful! "
                "<div class='message-info'>"
                "⏳ <strong>Waiting for Admin Approval</strong><br>"
                "📱 You will receive an SMS notification once your account is approved. "
                "Please wait for administrator approval before attempting to log in."
                "</div>"
            )
            messages.success(request, success_msg, extra_tags='registration')
            
            return redirect('login_page')
        else:
            # Don't add a generic error message - the form will display specific field errors
            pass
    else:
        form = FamilyMemberRegistrationForm()

    return render(request, 'register_member.html', {
        'form': form,
        'registration_type': 'member',
        'today': date.today(),
        'otp_enabled': OTP_VERIFICATION_ENABLED
    })
