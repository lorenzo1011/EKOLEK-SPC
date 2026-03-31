import json
import logging
import random
import string
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ==============================================================================
# PER-FEATURE OTP FLAGS (Production-Safe Configuration)
# ==============================================================================
OTP_LOGIN_ENABLED = getattr(settings, 'OTP_LOGIN_ENABLED', False)
OTP_REGISTER_ENABLED = getattr(settings, 'OTP_REGISTER_ENABLED', False)
OTP_RESET_PASSWORD_ENABLED = getattr(settings, 'OTP_RESET_PASSWORD_ENABLED', True)

# Legacy flag for backward compatibility
OTP_VERIFICATION_ENABLED = getattr(settings, 'OTP_VERIFICATION_ENABLED', True)

# Load API token and URL from Django settings with SAFE DEFAULTS
SMS_API_TOKEN = getattr(settings, 'SMS_API_TOKEN', '')
SMS_PROVIDER = getattr(settings, 'SMS_PROVIDER', 2)

# iProg Tech SMS API endpoint for sending OTP
SMS_API_URL = getattr(settings, 'SMS_API_URL', 'https://www.iprogsms.com/api/v1/sms_messages')

# Validate SMS credentials on import (log warning if missing but OTP enabled)
if OTP_RESET_PASSWORD_ENABLED and not SMS_API_TOKEN:
    logger.warning("SMS_API_TOKEN is missing but OTP is enabled for password reset!")
    logger.warning("Password reset via SMS will fail. Set SMS_API_TOKEN in environment.")

# ========================================
# OTP RATE LIMITING CONFIGURATION
# ========================================
OTP_FAILED_LOGIN_LIMIT = 3
OTP_FAILED_LOGIN_WINDOW_MINUTES = 60
OTP_MAX_VERIFY_ATTEMPTS = 5
OTP_COOLDOWN_MINUTES = 15
OTP_EXPIRY_MINUTES = 5


def _check_send_rate_limit(phone_number):
    """
    Check if phone number has exceeded failed login attempt limit.
    Only blocks OTP sending after multiple FAILED login attempts.
    Successful logins do NOT count towards this limit.

    Returns:
        dict: {'allowed': bool, 'error': str, 'retry_after': int}
    """
    failed_login_key = f'otp_failed_login_count_{phone_number}'
    cooldown_key = f'otp_failed_login_cooldown_{phone_number}'

    # Check if in cooldown period (locked due to too many failed attempts)
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Phone {phone_number} is locked due to failed login attempts. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many failed login attempts. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            cache.delete(cooldown_key)
            cache.delete(failed_login_key)

    # Check current failed login count
    failed_data = cache.get(failed_login_key)
    if failed_data:
        failed_info = json.loads(failed_data)
        count = failed_info.get('count', 0)

        if count >= OTP_FAILED_LOGIN_LIMIT:
            cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
            cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)

            logger.warning(f"[RATE LIMIT] Phone {phone_number} exceeded failed login limit ({count}/{OTP_FAILED_LOGIN_LIMIT}). Locked for {OTP_COOLDOWN_MINUTES}min")
            return {
                'allowed': False,
                'error': f'Too many failed login attempts. Please wait {OTP_COOLDOWN_MINUTES} minutes before trying again.',
                'retry_after': OTP_COOLDOWN_MINUTES * 60
            }

    logger.info(f"[RATE LIMIT] Phone {phone_number} allowed to request OTP")
    return {'allowed': True}


def _check_verify_rate_limit(phone_number):
    """
    Check if phone number has exceeded OTP verification attempt limit.

    Returns:
        dict: {'allowed': bool, 'error': str, 'attempts_left': int}
    """
    attempts_key = f'otp_verify_attempts_{phone_number}'
    cooldown_key = f'otp_verify_cooldown_{phone_number}'

    # Check if in verification cooldown
    cooldown_until = cache.get(cooldown_key)
    if cooldown_until:
        cooldown_time = datetime.fromisoformat(cooldown_until)
        if datetime.now() < cooldown_time:
            remaining_seconds = int((cooldown_time - datetime.now()).total_seconds())
            remaining_minutes = remaining_seconds // 60
            logger.warning(f"[RATE LIMIT] Phone {phone_number} is in verification cooldown. {remaining_minutes}min remaining")
            return {
                'allowed': False,
                'error': f'Too many failed verification attempts. Please wait {remaining_minutes} minutes before trying again.',
                'retry_after': remaining_seconds
            }
        else:
            cache.delete(cooldown_key)

    # Get current attempt count
    attempt_data = cache.get(attempts_key)
    if attempt_data:
        attempt_info = json.loads(attempt_data)
        count = attempt_info.get('count', 0)

        if count >= OTP_MAX_VERIFY_ATTEMPTS:
            cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
            cache.set(cooldown_key, cooldown_until.isoformat(), timeout=OTP_COOLDOWN_MINUTES * 60)
            cache.delete(attempts_key)

            logger.warning(f"[RATE LIMIT] Phone {phone_number} exceeded verification attempts ({count}/{OTP_MAX_VERIFY_ATTEMPTS}). Cooldown for {OTP_COOLDOWN_MINUTES}min")
            return {
                'allowed': False,
                'error': f'Too many failed attempts. Please wait {OTP_COOLDOWN_MINUTES} minutes before trying again.',
                'retry_after': OTP_COOLDOWN_MINUTES * 60
            }

        return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS - count}

    return {'allowed': True, 'attempts_left': OTP_MAX_VERIFY_ATTEMPTS}


def _increment_verify_attempts(phone_number):
    """Increment verification attempt counter"""
    attempts_key = f'otp_verify_attempts_{phone_number}'
    attempt_data = cache.get(attempts_key)

    if attempt_data:
        attempt_info = json.loads(attempt_data)
        attempt_info['count'] = attempt_info.get('count', 0) + 1
        attempt_info['last_attempt'] = datetime.now().isoformat()
    else:
        attempt_info = {
            'count': 1,
            'first_attempt': datetime.now().isoformat(),
            'last_attempt': datetime.now().isoformat()
        }

    cache.set(attempts_key, json.dumps(attempt_info), timeout=(OTP_EXPIRY_MINUTES + 5) * 60)
    logger.info(f"[RATE LIMIT] Phone {phone_number} verification attempts: {attempt_info['count']}/{OTP_MAX_VERIFY_ATTEMPTS}")


def _clear_verify_attempts(phone_number):
    """Clear verification attempt counter on successful verification"""
    attempts_key = f'otp_verify_attempts_{phone_number}'
    cache.delete(attempts_key)
    logger.info(f"[RATE LIMIT] Phone {phone_number} verification attempts cleared after successful verification")


def _increment_failed_login_attempts(phone_number):
    """Increment failed login attempt counter (called when OTP verification fails)"""
    failed_login_key = f'otp_failed_login_count_{phone_number}'
    failed_data = cache.get(failed_login_key)

    if failed_data:
        failed_info = json.loads(failed_data)
        failed_info['count'] = failed_info.get('count', 0) + 1
        failed_info['last_attempt'] = datetime.now().isoformat()
    else:
        failed_info = {
            'count': 1,
            'first_attempt': datetime.now().isoformat(),
            'last_attempt': datetime.now().isoformat()
        }

    cache.set(failed_login_key, json.dumps(failed_info), timeout=OTP_FAILED_LOGIN_WINDOW_MINUTES * 60)
    logger.info(f"[RATE LIMIT] Phone {phone_number} failed login attempts: {failed_info['count']}/{OTP_FAILED_LOGIN_LIMIT}")


def clear_failed_login_attempts(phone_number):
    """
    Clear failed login attempt counter on successful login.
    This function should be called from login views after successful authentication.

    Args:
        phone_number: The phone number to clear attempts for
    """
    failed_login_key = f'otp_failed_login_count_{phone_number}'
    cooldown_key = f'otp_failed_login_cooldown_{phone_number}'

    cache.delete(failed_login_key)
    cache.delete(cooldown_key)
    logger.info(f"[RATE LIMIT] Phone {phone_number} failed login attempts cleared after successful login")


def _generate_otp(length=6):
    """Generate a random numeric OTP code"""
    return ''.join(random.choices(string.digits, k=length))


def _store_otp(phone_number, otp_code, expires_in_minutes=None):
    """Store OTP in Redis cache with expiration time"""
    if expires_in_minutes is None:
        expires_in_minutes = OTP_EXPIRY_MINUTES

    expiry = datetime.now() + timedelta(minutes=expires_in_minutes)

    otp_data = {
        'otp': otp_code,
        'expires_at': expiry.isoformat(),
        'attempts': 0,
        'created_at': datetime.now().isoformat()
    }

    cache_key = f'otp_{phone_number}'
    cache.set(cache_key, json.dumps(otp_data), timeout=expires_in_minutes * 60)


def _verify_stored_otp(phone_number, otp_code):
    """Verify OTP from Redis cache with rate limiting"""
    # Check verification rate limit FIRST
    rate_limit = _check_verify_rate_limit(phone_number)
    if not rate_limit['allowed']:
        return {
            'success': False,
            'error': rate_limit['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }

    # Check if this OTP was recently verified (within last 2 minutes)
    verified_key = f'verified_{phone_number}'
    recently_verified = cache.get(verified_key)

    if recently_verified:
        verified_data = json.loads(recently_verified)
        verified_at = datetime.fromisoformat(verified_data['verified_at'])
        time_since_verify = datetime.now() - verified_at
        if time_since_verify < timedelta(minutes=2):
            return {'success': True, 'status': 'success', 'message': 'OTP verified successfully', 'already_verified': True}

    # Get OTP from Redis
    cache_key = f'otp_{phone_number}'
    stored_json = cache.get(cache_key)

    if not stored_json:
        _increment_verify_attempts(phone_number)
        _increment_failed_login_attempts(phone_number)
        return {'success': False, 'error': 'OTP not found or expired. Please request a new OTP.', 'error_type': 'otp_not_found'}

    stored_data = json.loads(stored_json)

    # Check expiration
    expires_at = datetime.fromisoformat(stored_data['expires_at'])
    if datetime.now() > expires_at:
        cache.delete(cache_key)
        _increment_verify_attempts(phone_number)
        _increment_failed_login_attempts(phone_number)
        return {'success': False, 'error': 'OTP has expired. Please request a new OTP.', 'error_type': 'otp_expired'}

    # Check OTP-specific attempts (legacy support - now using global rate limit)
    if stored_data.get('attempts', 0) >= 3:
        cache.delete(cache_key)
        return {'success': False, 'error': 'Too many failed attempts. Please request a new OTP.', 'error_type': 'too_many_attempts'}

    # Verify OTP
    if stored_data['otp'] == str(otp_code):
        cache.delete(cache_key)

        _clear_verify_attempts(phone_number)

        # Clear failed login attempts on successful OTP verification
        clear_failed_login_attempts(phone_number)

        # Track this as recently verified (cache for 2 minutes)
        verified_data = {
            'verified_at': datetime.now().isoformat(),
            'otp_code': otp_code
        }
        cache.set(verified_key, json.dumps(verified_data), timeout=120)

        return {'success': True, 'status': 'success', 'message': 'OTP verified successfully'}
    else:
        # Increment both OTP-specific attempts AND global verification attempts
        stored_data['attempts'] += 1
        cache.set(cache_key, json.dumps(stored_data), timeout=300)
        _increment_verify_attempts(phone_number)

        # Increment failed login attempts (this will trigger lockout after 3 failures)
        _increment_failed_login_attempts(phone_number)

        attempts_left = rate_limit.get('attempts_left', OTP_MAX_VERIFY_ATTEMPTS) - 1

        error_msg = f'Invalid OTP code. {attempts_left} attempts remaining.'
        if attempts_left == 0:
            error_msg = 'Invalid OTP code. No attempts remaining. Please wait before trying again.'

        return {
            'success': False,
            'error': error_msg,
            'error_type': 'invalid_otp',
            'attempts_left': attempts_left
        }


def _post_json(url, payload, timeout=10):
    headers = {'Content-Type': 'application/json'}
    try:
        logger.debug(f"Making POST request to OTP API: {url}")
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)

        logger.debug(f"OTP API Response - Status: {resp.status_code}")

        try:
            data = resp.json()
            logger.debug(f"Parsed OTP API response: {data}")
        except Exception:
            data = {}

        if data and isinstance(data, dict):
            status = str(data.get('status', '')).lower()
            message = str(data.get('message', '')).lower()

            if 'invalid' in message or 'incorrect' in message or 'wrong' in message:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            elif 'expired' in message or 'expire' in message:
                return {'success': False, 'error': 'OTP code has expired. Please request a new code.', 'error_type': 'expired_otp'}
            elif status == 'error' or status == 'fail' or status == 'failed':
                error_msg = data.get('message', 'Invalid OTP code. Please try again.')
                return {'success': False, 'error': error_msg, 'error_type': 'invalid_otp'}
            elif status in ('success', 'ok'):
                data['success'] = True
                return data

        resp.raise_for_status()

        if isinstance(data, dict):
            status_value = data.get('status')
            if status_value in ('success', 'ok', '200', 200, 'OK'):
                data['success'] = True
            elif 'success' in data:
                data['success'] = bool(data.get('success'))
            else:
                data['success'] = True
        return data
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None

        logger.error(f"HTTPError occurred: {e}")
        logger.error(f"Status code: {status_code}")
        if e.response:
            logger.debug(f"Response headers: {dict(e.response.headers)}")
            logger.debug(f"Response text: {e.response.text}")

        error_data = {}
        error_message = None
        try:
            error_data = e.response.json() if e.response else {}
            error_message = error_data.get('message') or error_data.get('error')
            logger.debug(f"Parsed error data: {error_data}")

            if error_message:
                error_msg_lower = str(error_message).lower()
                if 'invalid' in error_msg_lower or 'incorrect' in error_msg_lower or 'wrong' in error_msg_lower:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                elif 'expired' in error_msg_lower or 'expire' in error_msg_lower:
                    return {'success': False, 'error': 'OTP code has expired. Please request a new code.', 'error_type': 'expired_otp'}
        except Exception:
            error_message = None

        if status_code is None:
            return {'success': False, 'error': 'Unable to connect to SMS service. Please try again.', 'error_type': 'connection_error'}

        is_verify_request = 'verify_otp' in url if url else False

        if status_code == 401:
            if is_verify_request:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            else:
                return {'success': False, 'error': 'SMS service authentication failed. Please contact support.', 'error_type': 'auth_error'}
        elif status_code == 404:
            if is_verify_request:
                return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
            else:
                return {'success': False, 'error': 'OTP code not found or has expired. Please request a new code.', 'error_type': 'expired_otp'}
        elif status_code == 422:
            return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
        elif status_code == 429:
            return {'success': False, 'error': 'Too many OTP requests. Please wait a few minutes and try again.', 'error_type': 'rate_limit'}
        elif status_code == 400:
            if error_message and not any(word in str(error_message).lower() for word in ['http', 'api', 'url', 'unauthorized']):
                return {'success': False, 'error': str(error_message), 'error_type': 'bad_request'}
            else:
                if is_verify_request:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                else:
                    return {'success': False, 'error': 'Invalid phone number or OTP format. Please check and try again.', 'error_type': 'bad_request'}
        elif status_code >= 500:
            return {'success': False, 'error': 'SMS service is temporarily unavailable. Please try again later.', 'error_type': 'server_error'}
        else:
            if error_message and not any(word in str(error_message).lower() for word in ['http', 'api', 'url', 'unauthorized', '401', '404', '500']):
                return {'success': False, 'error': str(error_message), 'error_type': 'api_error'}
            else:
                if is_verify_request:
                    return {'success': False, 'error': 'Invalid OTP code. Please check and try again.', 'error_type': 'invalid_otp'}
                else:
                    return {'success': False, 'error': 'Unable to process OTP request. Please try again or contact support.', 'error_type': 'api_error'}
    except requests.exceptions.Timeout:
        logger.error("Request timeout occurred")
        return {'success': False, 'error': 'Request timeout. Please try again.', 'error_type': 'timeout'}
    except requests.exceptions.ConnectionError:
        logger.error("Connection error occurred")
        return {'success': False, 'error': 'Connection error. Please check your internet connection.', 'error_type': 'connection_error'}
    except Exception as e:
        logger.error(f"Unexpected error occurred: {type(e).__name__}: {str(e)}")
        return {'success': False, 'error': 'An unexpected error occurred. Please try again.', 'error_type': 'unknown_error'}


def send_otp(phone_number, message=None, purpose='login'):
    """
    Send OTP using iProg Tech SMS API with intelligent rate limiting

    Rate Limiting (Security Features):
    - Only blocks after 3 FAILED login attempts
    - Successful logins do NOT count towards limit
    - 15-minute cooldown after exceeding failed attempts
    - Successful OTP verification resets the counter to 0
    - Prevents brute force attacks while allowing legitimate users

    API Documentation: https://www.iprogsms.com/api/v1/sms_messages

    API Update (January 14, 2026):
    - Sender Name: 'iprogOTP' for OTP messages (daily limit active)
    - Fallback: 'iprogtech' (when daily limit exceeded)
    - Network Support: Globe/TM (Smart/TNT not supported by these sender names)
    - Automatic fallback ensures uninterrupted service

    Required Parameters:
    - api_token: Your API TOKEN
    - phone_number: Recipient's phone number (639XXXXXXXXX format)
    - message: SMS message content

    Optional Parameters:
    - sms_provider: SMS Provider (0, 1, or 2) | default: 2 for multi-network
    - purpose: Purpose of OTP ('login', 'registration', 'password_reset')

    Returns dict with API response:
    {
        "success": True/False,
        "status": 200,
        "message": "Your SMS message has been successfully added to the queue...",
        "message_id": "iSms-XHYBk",
        "data": {
            "otp_code": "123456",
            "otp_code_expires_at": "...",
            "phone_number": "639171074697"
        }
    }
    """
    # BYPASS MODE: Only bypass for login/registration, NOT for password_reset
    if not OTP_VERIFICATION_ENABLED and purpose in ['login', 'registration']:
        logger.info(f"[OTP BYPASS] OTP verification disabled for {purpose} - skipping SMS send")
        return {
            'success': True,
            'message': f'OTP verification disabled for {purpose} - bypass mode active',
            'bypass_mode': True,
            'data': {
                'otp_code': '000000',
                'phone_number': phone_number
            }
        }

    if not phone_number:
        return {'success': False, 'error': 'Missing phone number'}

    if not SMS_API_TOKEN:
        return {'success': False, 'error': 'SMS API token not configured'}

    # Format phone number to 639XXXXXXXXX (iProg SMS API format)
    phone_clean = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    phone_clean = ''.join(filter(str.isdigit, phone_clean))

    if phone_clean.startswith('09'):
        phone_formatted = '63' + phone_clean[1:]
    elif phone_clean.startswith('9') and len(phone_clean) == 10:
        phone_formatted = '63' + phone_clean
    elif phone_clean.startswith('639'):
        phone_formatted = phone_clean
    elif phone_clean.startswith('63') and len(phone_clean) == 12:
        phone_formatted = phone_clean
    else:
        if len(phone_clean) == 10 and phone_clean.startswith('9'):
            phone_formatted = '63' + phone_clean
        else:
            return {'success': False, 'error': 'Invalid phone number format'}

    # CHECK RATE LIMIT BEFORE SENDING
    rate_limit_check = _check_send_rate_limit(phone_formatted)
    if not rate_limit_check['allowed']:
        return {
            'success': False,
            'error': rate_limit_check['error'],
            'error_type': 'rate_limit',
            'retry_after': rate_limit_check.get('retry_after', OTP_COOLDOWN_MINUTES * 60)
        }

    # Generate OTP code
    otp_code = _generate_otp(6)

    # Store OTP for later verification
    _store_otp(phone_formatted, otp_code, expires_in_minutes=OTP_EXPIRY_MINUTES)

    # Build OTP message
    if message and ':otp' in message:
        otp_message = message.replace(':otp', otp_code)
    else:
        otp_message = (
            f"Your E-KOLEK verification code is: {otp_code}\n"
            f"This code is valid for 5 minutes.\n"
            f"Do not share this code with anyone.\n"
            f"- E-KOLEK Team"
        )

    # Build payload for SMS API
    payload = {
        'api_token': SMS_API_TOKEN,
        'phone_number': phone_formatted,
        'message': otp_message,
        'sms_provider': SMS_PROVIDER,
        'sender_name': 'iprogOTP'
    }

    result = _post_json(SMS_API_URL, payload)

    # Transform SMS API response to match OTP service interface
    if isinstance(result, dict):
        if result.get('success') or result.get('status') == 200:
            expires_at = (datetime.now() + timedelta(minutes=5)).isoformat()

            result['success'] = True
            result['data'] = {
                'otp_code': otp_code,
                'otp_code_expires_at': expires_at,
                'otp_code_confirmed': False,
                'phone_number': phone_formatted,
                'message': otp_message
            }
        else:
            result['success'] = False

    return result


def verify_otp(phone_number, otp_code, purpose='login'):
    """
    Verify OTP using local storage (no API call needed)

    Since we're using SMS API to send OTPs, we manage verification locally.
    The OTP is stored in memory when sent and verified here.

    Phone format: Must match the format used in send_otp (639XXXXXXXXX)

    Parameters:
    - phone_number: Phone number to verify
    - otp_code: OTP code to verify
    - purpose: Purpose of verification ('login', 'registration', 'password_reset')

    Returns dict with verification result:
    {
        "status": "success",
        "message": "OTP verified successfully"
    }
    """
    # BYPASS MODE: Only bypass for login/registration, NOT for password_reset
    if not OTP_VERIFICATION_ENABLED and purpose in ['login', 'registration']:
        logger.info(f"[OTP BYPASS] OTP verification disabled for {purpose} - auto-approving")
        return {
            'success': True,
            'status': 'success',
            'message': f'OTP verification disabled for {purpose} - bypass mode active',
            'bypass_mode': True
        }

    if not phone_number or not otp_code:
        return {'success': False, 'error': 'Missing phone number or otp'}

    # Format phone number to 639XXXXXXXXX (SAME FORMAT AS SEND_OTP)
    phone_clean = phone_number.strip().replace(' ', '').replace('-', '').replace('+', '')
    phone_clean = ''.join(filter(str.isdigit, phone_clean))

    if phone_clean.startswith('09'):
        phone_formatted = '63' + phone_clean[1:]
    elif phone_clean.startswith('9') and len(phone_clean) == 10:
        phone_formatted = '63' + phone_clean
    elif phone_clean.startswith('639'):
        phone_formatted = phone_clean
    elif phone_clean.startswith('63') and len(phone_clean) == 12:
        phone_formatted = phone_clean
    else:
        if len(phone_clean) == 10 and phone_clean.startswith('9'):
            phone_formatted = '63' + phone_clean
        else:
            phone_formatted = phone_clean

    # Verify OTP from local storage
    result = _verify_stored_otp(phone_formatted, otp_code)

    return result


def list_otps():
    """
    List stored OTPs from Redis (for debugging purposes only)
    Returns list of active OTPs in cache

    Note: This is a simple implementation. In production with many OTPs,
    consider maintaining a separate index or using Redis SCAN command.
    """
    return {
        'success': True,
        'message': 'OTP listing disabled - OTPs are stored in Redis with individual keys',
        'count': 0,
        'otps': []
    }
