# Mobile App OTP Bypass Documentation

**Internal Technical Documentation**  
*For Development Team Only - Do Not Push to Public Repository*

---

## Table of Contents
1. [Overview](#overview)
2. [Backend Implementation](#backend-implementation)
3. [Mobile App Changes](#mobile-app-changes)
4. [Configuration Guide](#configuration-guide)
5. [Testing Procedures](#testing-procedures)
6. [Security Considerations](#security-considerations)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is OTP Bypass?

The E-KOLEK system includes a **feature flag** that allows you to completely disable OTP (One-Time Password) verification for mobile app login. When disabled, users can log in directly with their username and password without receiving or entering an OTP code.

### Current Status
- **Web Login**: OTP is currently **DISABLED** (users login directly)
- **Mobile App Login**: OTP can be **ENABLED or DISABLED** via environment variable
- **Configuration Location**: `eko/settings.py` and Railway environment variables

### When to Use OTP Bypass
✅ **Use OTP Bypass When:**
- Testing login flows during development
- SMS service is unavailable or too expensive
- Users don't have reliable phone access
- Debugging authentication issues

❌ **Don't Use OTP Bypass When:**
- Deploying to production (security risk)
- Handling sensitive user data
- Compliance requirements mandate 2FA

---

## Backend Implementation

### 1. Feature Flag Configuration

**File**: `eko/settings.py` (Line 306)
```python
# OTP Verification Feature Flag
# Set to False to disable OTP verification system-wide
OTP_VERIFICATION_ENABLED = config('OTP_VERIFICATION_ENABLED', default=True, cast=bool)
```

**How It Works:**
- Reads from environment variable `OTP_VERIFICATION_ENABLED`
- Defaults to `True` (OTP enabled) if not set
- Uses `decouple` library to cast string to boolean
- Available globally via `django.conf.settings`

### 2. Mobile Login Endpoints

The mobile app uses **JWT tokens** for authentication. Two login endpoints support OTP bypass:

#### **Endpoint 1: Standard Login** (`/api/login/`)

**File**: `mobilelogin/django_otp_views.py` (Lines 21-108)

**Normal Flow (OTP Enabled):**
```
User → POST username/password → Server validates → Sends OTP → Returns user_id
User → POST user_id/otp → Server verifies OTP → Returns JWT token
```

**Bypass Flow (OTP Disabled):**
```python
if not OTP_VERIFICATION_ENABLED:
    logger.info(f"[OTP BYPASS] Skipping OTP for user {user.username} - issuing token directly")
    
    # Delete existing tokens and create new one
    Token.objects.filter(user=user).delete()
    token = Token.objects.create(user=user)
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Return token immediately
    return Response({
        'success': True,
        'message': 'Login successful (OTP disabled)',
        'otp_bypassed': True,  # Flag for mobile app
        'token': token.key,
        'user_info': { ... },
        'family_info': { ... }
    }, status=200)
```

**Key Changes:**
- Skips `otp_service.send_otp()` call
- Creates `rest_framework.authtoken.models.Token` directly
- Returns `otp_bypassed: true` flag so mobile app knows OTP was skipped
- Includes full user and family info in single response

#### **Endpoint 2: QR Login** (`/api/qr-login/`)

**File**: `mobilelogin/django_otp_views.py` (Lines 116-217)

**Same bypass logic applies:**
```python
if not OTP_VERIFICATION_ENABLED:
    logger.info(f"[OTP BYPASS] Skipping OTP for QR login user {user.username} - issuing token directly")
    # ... (identical token creation logic)
```

**Additional QR Features:**
- Accepts username, user_id, or family_code
- Returns `via` field indicating search method used
- Full bypass support with immediate token issuance

### 3. Response Format Changes

**With OTP Enabled (2-step flow):**
```json
// Step 1: POST /api/login/
{
  "success": true,
  "otp_sent": true,
  "user_id": "12345678-1234-1234-1234-123456789abc"
}

// Step 2: POST /api/login/verify-otp/
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user_info": { ... },
  "family_info": { ... }
}
```

**With OTP Disabled (1-step flow):**
```json
// Single Step: POST /api/login/
{
  "success": true,
  "message": "Login successful (OTP disabled)",
  "otp_bypassed": true,  // ← Key flag!
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",  // ← DRF Token (not JWT)
  "user_info": {
    "id": "12345678-1234-1234-1234-123456789abc",
    "username": "juan_delaCruz",
    "full_name": "Juan Dela Cruz",
    "total_points": 250,
    "status": "approved"
  },
  "family_info": {
    "id": "87654321-4321-4321-4321-cba987654321",
    "family_name": "Dela Cruz Family",
    "family_code": "DLCRZ-2024",
    "barangay": "Barangay San Roque"
  }
}
```

---

## Mobile App Changes

### 1. Login Flow Modifications

**Current Mobile Implementation** (Assumed Flutter/Dart):

```dart
// ❌ OLD CODE (2-step OTP flow)
Future<bool> login(String username, String password) async {
  // Step 1: Send credentials
  final response = await http.post(
    Uri.parse('$baseUrl/api/login/'),
    body: {'username': username, 'password': password}
  );
  
  if (response['success'] && response['otp_sent']) {
    String userId = response['user_id'];
    // Navigate to OTP screen
    return false; // Wait for OTP
  }
}

Future<bool> verifyOtp(String userId, String otp) async {
  // Step 2: Verify OTP
  final response = await http.post(
    Uri.parse('$baseUrl/api/login/verify-otp/'),
    body: {'user_id': userId, 'otp': otp}
  );
  
  if (response['success']) {
    saveToken(response['access_token']);
    return true;
  }
}
```

**✅ NEW CODE (OTP bypass support):**

```dart
Future<bool> login(String username, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/api/login/'),
    body: {'username': username, 'password': password}
  );
  
  if (response['success']) {
    // Check if OTP was bypassed
    if (response['otp_bypassed'] == true) {
      // OTP DISABLED: Login complete in one step
      saveToken(response['token']);  // Use 'token' field (DRF Token)
      saveUserData(response['user_info']);
      saveFamilyData(response['family_info']);
      return true;  // Navigate to home screen
    } 
    else if (response['otp_sent'] == true) {
      // OTP ENABLED: Continue to OTP verification screen
      String userId = response['user_id'];
      navigateToOtpScreen(userId);
      return false;
    }
  }
  
  return false; // Login failed
}
```

### 2. Token Storage Changes

**CRITICAL DIFFERENCE:**

| Feature | OTP Enabled | OTP Disabled |
|---------|------------|--------------|
| **Token Type** | JWT (JSON Web Token) | DRF Token (Django REST Framework Token) |
| **Access Token Field** | `access_token` | `token` |
| **Refresh Token Field** | `refresh_token` | ❌ Not provided |
| **Token Header** | `Authorization: Bearer <jwt>` | `Authorization: Token <token>` |
| **Expires** | Yes (1 hour) | ❌ Never expires |

**Mobile App Token Service:**

```dart
class TokenService {
  String? _tokenType;  // 'jwt' or 'drf'
  String? _accessToken;
  String? _refreshToken;
  
  void saveLoginResponse(Map<String, dynamic> response) {
    if (response['otp_bypassed'] == true) {
      // OTP disabled - DRF Token
      _tokenType = 'drf';
      _accessToken = response['token'];
      _refreshToken = null;
    } else {
      // OTP enabled - JWT Token
      _tokenType = 'jwt';
      _accessToken = response['access_token'];
      _refreshToken = response['refresh_token'];
    }
    
    // Save to secure storage
    saveToStorage('token_type', _tokenType);
    saveToStorage('access_token', _accessToken);
    if (_refreshToken != null) {
      saveToStorage('refresh_token', _refreshToken);
    }
  }
  
  String getAuthorizationHeader() {
    if (_tokenType == 'jwt') {
      return 'Bearer $_accessToken';
    } else {
      return 'Token $_accessToken';
    }
  }
}
```

### 3. API Request Headers

**All subsequent API calls must use correct header format:**

```dart
Future<Map<String, dynamic>> apiRequest(String endpoint) async {
  final tokenService = TokenService();
  
  final response = await http.get(
    Uri.parse('$baseUrl$endpoint'),
    headers: {
      'Authorization': tokenService.getAuthorizationHeader(),  // ← Auto-detects format
      'Content-Type': 'application/json',
    }
  );
  
  return jsonDecode(response.body);
}
```

---

## Configuration Guide

### Step 1: Update Railway Environment Variables

1. **Login to Railway Dashboard**
   - Go to: https://railway.app/
   - Select your E-KOLEK project

2. **Navigate to Variables Tab**
   - Click on your Django service
   - Click "Variables" in the left sidebar

3. **Add or Update Variable**
   ```
   Variable Name: OTP_VERIFICATION_ENABLED
   Variable Value: False
   ```

4. **Deploy Changes**
   - Click "Add Variable" or "Update"
   - Railway will automatically redeploy your app
   - Wait 2-3 minutes for deployment to complete

### Step 2: Verify Backend Configuration

**Test with curl:**
```bash
# Test login endpoint
curl -X POST https://your-app.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "test_password"
  }'

# Expected response when OTP is DISABLED:
{
  "success": true,
  "message": "Login successful (OTP disabled)",
  "otp_bypassed": true,
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_info": { ... }
}
```

### Step 3: Update Mobile App Code

1. **Update Login Service** (see code examples above)
2. **Update Token Storage** (handle both JWT and DRF tokens)
3. **Update Authorization Headers** (Bearer vs Token prefix)
4. **Test Both Modes** (with OTP enabled and disabled)

### Step 4: Local Development Setup

**For local testing, create `.env` file:**
```bash
# .env file in project root
OTP_VERIFICATION_ENABLED=False
```

**Start local server:**
```bash
python manage.py runserver
```

---

## Testing Procedures

### Backend Testing Checklist

✅ **Test 1: Standard Login (OTP Disabled)**
```bash
# Request
POST /api/login/
{
  "username": "juan_delaCruz",
  "password": "SecurePassword123"
}

# Expected Response
{
  "success": true,
  "otp_bypassed": true,
  "token": "abc123...",
  "user_info": {...}
}
```

✅ **Test 2: QR Login (OTP Disabled)**
```bash
# Request
POST /api/qr-login/
{
  "qr_code": "juan_delaCruz"
}

# Expected Response
{
  "success": true,
  "otp_bypassed": true,
  "via": "username",
  "token": "xyz789...",
  "user_info": {...}
}
```

✅ **Test 3: Protected Endpoint Access**
```bash
# Request
GET /api/current_user_data/
Headers:
  Authorization: Token abc123...

# Expected Response
{
  "success": true,
  "user_data": {...}
}
```

✅ **Test 4: Invalid Credentials**
```bash
# Request
POST /api/login/
{
  "username": "wrong_user",
  "password": "wrong_password"
}

# Expected Response
{
  "success": false,
  "message": "Invalid username or password",
  "error_code": "INVALID_CREDENTIALS"
}
```

### Mobile App Testing Checklist

✅ **Test 1: Login Flow**
- [ ] App sends username/password to `/api/login/`
- [ ] App receives `otp_bypassed: true` flag
- [ ] App saves DRF token (not JWT)
- [ ] App navigates directly to home screen (skips OTP screen)
- [ ] No OTP SMS is sent to user

✅ **Test 2: QR Scan Login**
- [ ] App scans QR code
- [ ] App sends QR code to `/api/qr-login/`
- [ ] App receives token immediately
- [ ] App navigates to home screen

✅ **Test 3: API Calls After Login**
- [ ] Test GET `/api/current_user_data/`
- [ ] Test GET `/api/current_points/`
- [ ] Test GET `/api/family_members/`
- [ ] All requests use `Authorization: Token <token>` header

✅ **Test 4: Logout and Re-login**
- [ ] User logs out
- [ ] App clears token from storage
- [ ] User logs in again
- [ ] New token is issued

### Re-enabling OTP Testing

**To test with OTP enabled:**
1. Set `OTP_VERIFICATION_ENABLED=True` in Railway
2. Redeploy
3. Mobile app should:
   - Receive `otp_sent: true` instead of `otp_bypassed: true`
   - Navigate to OTP verification screen
   - Wait for user to enter OTP
   - Call `/api/login/verify-otp/` with user_id and otp
   - Receive JWT tokens (not DRF token)

---

## Security Considerations

### ⚠️ Important Security Notes

1. **OTP Bypass is LESS Secure**
   - Single-factor authentication only (password)
   - No protection against stolen passwords
   - Not recommended for production

2. **Token Management**
   - DRF tokens **never expire** automatically
   - JWT tokens expire after 1 hour
   - Use JWT (OTP enabled) for better security

3. **Logging and Monitoring**
   - All OTP bypass logins are logged with `[OTP BYPASS]` prefix
   - Check logs regularly: `railway logs --service django`
   - Monitor for suspicious login patterns

4. **Environment Variables**
   - **NEVER** commit OTP_VERIFICATION_ENABLED=False to Git
   - Use environment-specific variables
   - Production should ALWAYS have OTP enabled

### Best Practices

✅ **DO:**
- Use OTP bypass only in development/staging
- Log all bypass login attempts
- Document why OTP is disabled
- Have a plan to re-enable OTP

❌ **DON'T:**
- Deploy to production with OTP disabled
- Share bypass tokens publicly
- Store tokens in plaintext
- Hardcode OTP_VERIFICATION_ENABLED=False in code

---

## Troubleshooting

### Problem 1: Mobile App Still Asking for OTP

**Symptoms:**
- Backend has `OTP_VERIFICATION_ENABLED=False`
- Mobile app still shows OTP input screen

**Solutions:**
1. **Check if mobile app is using old endpoint:**
   ```dart
   // ❌ Wrong - using old non-bypass endpoint
   POST /api/login/  // From mobilelogin/auth_views.py (no bypass)
   
   // ✅ Correct - using bypass-aware endpoint
   POST /api/login/  // From mobilelogin/django_otp_views.py (has bypass)
   ```

2. **Verify URL routing in `mobilelogin/urls.py`:**
   ```python
   # Line 13 - Should import from django_otp_views for bypass support
   from . import django_otp_views  # ← Not from auth_views
   
   urlpatterns = [
       path('api/login/', django_otp_views.login_view, name='api_login'),  # ← Uses bypass logic
   ]
   ```

3. **Check mobile app code:**
   ```dart
   // Must check for 'otp_bypassed' flag
   if (response['otp_bypassed'] == true) {
     // Skip OTP screen
   }
   ```

### Problem 2: "Invalid Token" Error After Login

**Symptoms:**
- Login succeeds with `otp_bypassed: true`
- Subsequent API calls return 401 Unauthorized

**Solutions:**
1. **Check Authorization header format:**
   ```dart
   // ❌ Wrong - using JWT format with DRF token
   headers: {'Authorization': 'Bearer $token'}
   
   // ✅ Correct - using Token format with DRF token
   headers: {'Authorization': 'Token $token'}
   ```

2. **Verify token field:**
   ```dart
   // ❌ Wrong - trying to use JWT field
   String token = response['access_token'];  // null when bypassed
   
   // ✅ Correct - using DRF token field
   String token = response['token'];  // exists when bypassed
   ```

### Problem 3: Railway Deployment Not Picking Up Variable

**Symptoms:**
- Added `OTP_VERIFICATION_ENABLED=False` to Railway
- Backend still sends OTP

**Solutions:**
1. **Force redeploy:**
   ```bash
   railway up --service django
   ```

2. **Check variable is set:**
   ```bash
   railway variables --service django
   # Should show: OTP_VERIFICATION_ENABLED = False
   ```

3. **Check settings.py is reading variable:**
   ```python
   # In eko/settings.py
   print(f"OTP_VERIFICATION_ENABLED: {OTP_VERIFICATION_ENABLED}")  # Should print False
   ```

4. **Verify using logs:**
   ```bash
   railway logs --service django
   # Look for: [OTP BYPASS] Skipping OTP for user...
   ```

### Problem 4: Can't Switch Back to OTP Enabled

**Symptoms:**
- Changed `OTP_VERIFICATION_ENABLED=True`
- Mobile app still receives `otp_bypassed: true`

**Solutions:**
1. **Clear mobile app cache:**
   - Uninstall and reinstall app
   - Clear app data
   - Force stop app

2. **Restart Railway service:**
   ```bash
   railway restart --service django
   ```

3. **Verify backend logs:**
   ```bash
   railway logs --service django | grep "OTP"
   # Should NOT see [OTP BYPASS] messages
   ```

### Problem 5: Different Endpoints Using Different Logic

**Issue:**
There are TWO sets of mobile login views:

1. **`mobilelogin/auth_views.py`** - **NO OTP bypass support**
2. **`mobilelogin/django_otp_views.py`** - **HAS OTP bypass support**

**Solution:**
Always import from `django_otp_views.py` for bypass support:

```python
# mobilelogin/urls.py
from . import django_otp_views  # ← Correct (has bypass)
# from . import auth_views  # ← Wrong (no bypass)

urlpatterns = [
    path('api/login/', django_otp_views.login_view, ...),  # ✅
    path('api/qr-login/', django_otp_views.qr_login, ...),  # ✅
]
```

---

## Summary

### Quick Reference

| Aspect | OTP Enabled | OTP Disabled |
|--------|-------------|--------------|
| **Environment Variable** | `OTP_VERIFICATION_ENABLED=True` | `OTP_VERIFICATION_ENABLED=False` |
| **Login Steps** | 2-step (credentials → OTP) | 1-step (credentials only) |
| **SMS Sent** | ✅ Yes | ❌ No |
| **Token Type** | JWT | DRF Token |
| **Token Field** | `access_token` | `token` |
| **Auth Header** | `Bearer <jwt>` | `Token <token>` |
| **Response Flag** | `otp_sent: true` | `otp_bypassed: true` |
| **Security Level** | 🔒 High (2FA) | ⚠️ Medium (1FA) |

### Key Files Modified

1. **`eko/settings.py`** (Line 306) - Feature flag configuration
2. **`mobilelogin/django_otp_views.py`** (Lines 21-217) - Bypass logic for login/QR
3. **`mobilelogin/urls.py`** (Line 13) - Endpoint routing

### Mobile App Changes Required

1. Check `otp_bypassed` flag in login response
2. Handle both DRF Token and JWT token types
3. Use correct Authorization header format
4. Skip OTP screen when `otp_bypassed: true`

---

## Contact

For questions or issues with OTP bypass implementation:
- Review this documentation
- Check Railway logs: `railway logs --service django`
- Test with curl before modifying mobile app
- Ensure `django_otp_views.py` is being used (not `auth_views.py`)

**Last Updated**: January 2025  
**Document Version**: 1.0  
**Status**: Internal Use Only - Do Not Distribute
