"""
Security middleware for additional protection.

Provides brute-force prevention, admin access control,
and input sanitization (SQL injection / XSS detection).
"""

import hashlib

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from eko.constants import LOGIN_ATTEMPT_WINDOW_MINUTES, MAX_LOGIN_ATTEMPTS
from eko.security_utils import get_client_ip, log_security_event


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds security headers to all responses
    """
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'  # Less restrictive to allow icons
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Don't add CSP header if CSP middleware is active (it will handle it)
        # The CSP middleware will use CONTENT_SECURITY_POLICY from settings.py
        
        return response


class BruteForceProtectionMiddleware(MiddlewareMixin):
    """
    Protects against brute force attacks on login endpoints
    """
    def process_request(self, request):
        """Block requests from IPs that exceed the login attempt threshold."""
        if request.path in ['/accounts/login/', '/accounts/qr_login/']:
            ip = get_client_ip(request)
            cache_key = f"login_attempts_{hashlib.md5(ip.encode()).hexdigest()}"

            attempts = cache.get(cache_key, 0)

            if attempts >= MAX_LOGIN_ATTEMPTS:
                log_security_event(
                    'BRUTE_FORCE_BLOCKED',
                    ip_address=ip,
                    details=f'Path: {request.path}'
                )
                return JsonResponse({'error': 'Too many login attempts. Try again later.'}, status=429)

            if request.method == 'POST':
                timeout = LOGIN_ATTEMPT_WINDOW_MINUTES * 60
                cache.set(cache_key, attempts + 1, timeout=timeout)

        return None


class AdminAccessControlMiddleware(MiddlewareMixin):
    """
    Additional access control for admin pages
    """
    ADMIN_PATHS = [
        '/cenro/admincontrol/',
        '/cenro/adminuser/',
        '/cenro/adminpoints/',
        '/cenro/adminrewards/',
        '/cenro/adminschedule/',
        '/cenro/admingames/',
        '/cenro/adminquiz/',
        '/cenro/adminlearn/',
    ]
    
    # API endpoints that use custom admin authentication (session-based)
    API_ADMIN_PATHS = [
        '/game/',  # Admin game endpoints - MOVED OUT OF /api/ to avoid DRF
    ]
    
    def process_request(self, request):
        # Check if accessing API endpoint - use custom admin session auth
        for api_path in self.API_ADMIN_PATHS:
            if request.path.startswith(api_path):
                # Check custom admin session authentication
                if not request.session.get('admin_user_id'):
                    log_security_event(
                        'UNAUTHORIZED_API_ACCESS',
                        ip_address=get_client_ip(request),
                        details=f'Path: {request.path} - No admin_user_id in session'
                    )
                    return JsonResponse({'error': 'Admin authentication required'}, status=401)
                
                # Log admin API access
                if request.method == 'POST':
                    log_security_event(
                        'ADMIN_API_ACTION',
                        ip_address=get_client_ip(request),
                        details=f'Admin: {request.session.get("admin_username")} - Path: {request.path}'
                    )
                
                return None  # Allow request to proceed
        
        # Check if accessing admin page (HTML pages)
        for admin_path in self.ADMIN_PATHS:
            if request.path.startswith(admin_path):
                # Log unauthorized access attempts for monitoring.
                # The @admin_required decorator handles blocking/redirect.
                if not request.session.get('admin_user_id'):
                    log_security_event(
                        'UNAUTHORIZED_ADMIN_ACCESS',
                        ip_address=get_client_ip(request),
                        details=f'Path: {request.path} - No admin session'
                    )
                elif request.method == 'POST':
                    log_security_event(
                        'ADMIN_ACTION',
                        ip_address=get_client_ip(request),
                        details=f'Admin: {request.session.get("admin_username")} - Path: {request.path}'
                    )
        
        return None


class InputSanitizationMiddleware(MiddlewareMixin):
    """
    Detects potential SQL injection and XSS attempts in request parameters.
    """
    SUSPICIOUS_PATTERNS = [
        'union select', 'drop table', 'delete from', 'insert into',
        'update set', '--', '/*', '*/', 'xp_cmdshell', 'sp_executesql',
        'exec(', 'execute(', 'script>', '<script', 'javascript:',
        'onload=', 'onerror=', 'onclick='
    ]
    
    # Whitelist paths that handle legitimate long-text content
    WHITELISTED_PATHS = [
        '/admincontrol/add-terms/',
        '/admincontrol/edit-terms/',
        '/api/extract-file-content/',
    ]
    
    def process_request(self, request):
        # Skip scanning for whitelisted admin endpoints
        for whitelist_path in self.WHITELISTED_PATHS:
            if request.path.startswith(whitelist_path):
                return None
        
        # Check GET parameters
        for key, value in request.GET.items():
            if self._contains_suspicious_content(value.lower()):
                log_security_event(
                    'SQL_INJECTION_ATTEMPT',
                    ip_address=get_client_ip(request),
                    details=f'GET param {key}: {value[:100]}'
                )
                return JsonResponse({'error': 'Invalid request'}, status=400)
        
        # Check POST parameters
        if hasattr(request, 'POST'):
            for key, value in request.POST.items():
                if isinstance(value, str) and self._contains_suspicious_content(value.lower()):
                    log_security_event(
                        'SQL_INJECTION_ATTEMPT',
                        ip_address=get_client_ip(request),
                        details=f'POST param {key}: {value[:100]}'
                    )
                    return JsonResponse({'error': 'Invalid request'}, status=400)
        
        return None
    
    def _contains_suspicious_content(self, content):
        """Check if content contains suspicious patterns"""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in content:
                return True
        return False
