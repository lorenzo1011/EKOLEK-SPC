# Flutter App Implementation Guide: OTP Disabled Mode

**How to Implement Login Without OTP in Your Flutter Mobile App**

---

## 🎯 Quick Overview

### Current Backend State
- ✅ **OTP is DISABLED** on the backend (Railway environment: `OTP_VERIFICATION_ENABLED=False`)
- ✅ No SMS OTP codes are being sent
- ✅ Login happens in **ONE STEP**: Username + Password → Immediate access
- ✅ Backend returns DRF Token (not JWT)

### What Your Flutter App Must Do
1. Send username + password to `/api/login/`
2. Check response for `otp_bypassed: true` flag
3. **Skip OTP screen entirely** when flag is present
4. Save the DRF Token
5. Navigate directly to home screen
6. Use `Token` authentication header (not `Bearer`)

---

## 📝 Step-by-Step Implementation

### Step 1: Update Login Logic

**Current login flow (with OTP):**
```dart
// ❌ OLD FLOW (Don't use this)
1. POST /api/login/ → Get user_id
2. Navigate to OTP screen
3. POST /api/login/verify-otp/ → Get JWT token
4. Navigate to home
```

**New login flow (OTP disabled):**
```dart
// ✅ NEW FLOW (Use this)
1. POST /api/login/ → Check otp_bypassed flag
2. If otp_bypassed = true → Save token → Navigate to home
3. If otp_sent = true → Navigate to OTP screen (backward compatible)
```

### Step 2: Modify Your Auth Service

**Update your `auth_service.dart` login method:**

```dart
// lib/services/auth_service.dart

Future<LoginResult> login(String username, String password) async {
  try {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}/api/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username.trim(),
        'password': password,
      }),
    ).timeout(Duration(seconds: 30));

    final data = jsonDecode(response.body);

    if (response.statusCode == 200 && data['success'] == true) {
      
      // ⭐ CHECK THIS FLAG - This is the key difference
      if (data['otp_bypassed'] == true) {
        // 🎉 OTP IS DISABLED - Login complete in one step!
        
        // Save DRF Token (not JWT)
        await _storage.saveToken(data['token']);
        await _storage.saveTokenType('drf');
        
        // Save user data
        if (data['user_info'] != null) {
          await _storage.saveUserData(data['user_info']);
          await _storage.saveUserId(data['user_info']['id']);
        }
        
        // Save family data
        if (data['family_info'] != null) {
          await _storage.saveFamilyData(data['family_info']);
        }
        
        return LoginResult(
          success: true,
          otpRequired: false,  // ← No OTP needed!
          message: data['message'] ?? 'Login successful',
        );
      } 
      else if (data['otp_sent'] == true) {
        // OTP is enabled - need verification (backward compatibility)
        return LoginResult(
          success: true,
          otpRequired: true,
          userId: data['user_id'],
          message: 'OTP sent to your phone',
        );
      }
    }

    // Login failed
    return LoginResult(
      success: false,
      message: data['message'] ?? 'Login failed',
      errorCode: data['error_code'],
    );

  } catch (e) {
    return LoginResult(
      success: false,
      message: 'Connection error: ${e.toString()}',
    );
  }
}
```

### Step 3: Update Login Screen Navigation

**Modify your login button handler:**

```dart
// lib/screens/auth/login_screen.dart

Future<void> _handleLogin() async {
  if (!_formKey.currentState!.validate()) return;

  setState(() => _isLoading = true);

  try {
    final result = await _authService.login(
      _usernameController.text,
      _passwordController.text,
    );

    if (!mounted) return;

    if (result.success) {
      
      // ⭐ KEY DECISION POINT
      if (result.otpRequired) {
        // OTP is enabled - show OTP verification screen
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => OtpVerifyScreen(
              userId: result.userId!,
            ),
          ),
        );
      } else {
        // ✅ OTP is DISABLED - go directly to home
        // Login is already complete!
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const HomeScreen(),
          ),
        );
        
        // Optional: Show success message
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Welcome back!'),
            backgroundColor: Colors.green,
          ),
        );
      }
      
    } else {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.message),
          backgroundColor: Colors.red,
        ),
      );
    }
    
  } finally {
    if (mounted) {
      setState(() => _isLoading = false);
    }
  }
}
```

### Step 4: Update Authorization Header

**CRITICAL: Use correct header format for DRF Token**

```dart
// lib/services/storage_service.dart

/// Get authorization header for API requests
Future<String?> getAuthorizationHeader() async {
  final token = await getToken();
  if (token == null) return null;
  
  final tokenType = await getTokenType();
  
  // ⚠️ IMPORTANT: Different header formats
  if (tokenType == 'jwt') {
    // JWT Token (when OTP is enabled)
    return 'Bearer $token';
  } else {
    // ✅ DRF Token (when OTP is disabled)
    return 'Token $token';  // ← Notice: "Token" not "Bearer"
  }
}
```

### Step 5: Update All API Calls

**Use the authorization header in all API requests:**

```dart
// lib/services/api_service.dart

Future<ApiResponse> get(String endpoint) async {
  try {
    final authHeader = await _storage.getAuthorizationHeader();
    if (authHeader == null) {
      return ApiResponse(
        success: false,
        message: 'Not authenticated',
        statusCode: 401,
      );
    }

    // ✅ Use the correct header format automatically
    final response = await http.get(
      Uri.parse('${ApiConfig.baseUrl}$endpoint'),
      headers: {
        'Authorization': authHeader,  // ← "Token abc..." when OTP disabled
        'Content-Type': 'application/json',
      },
    ).timeout(ApiConfig.connectionTimeout);

    return _handleResponse(response);
  } catch (e) {
    return ApiResponse(
      success: false,
      message: 'Network error: ${e.toString()}',
    );
  }
}
```

---

## 🔐 Security Considerations (OTP Disabled)

### What Security Measures Are Still Active?

✅ **Password-Based Authentication**
- Users must provide correct username and password
- Password minimum length enforced (6 characters)
- Account must be approved by admin

✅ **Token-Based Sessions**
- DRF Token is cryptographically secure
- Token required for all API requests
- Token stored in secure storage

✅ **Backend Validations**
- User status must be "approved"
- Family status must be "approved"
- Account must be active
- Phone number must be registered

✅ **Secure Storage**
- Flutter Secure Storage for tokens
- Data encrypted at rest
- No plain text credentials stored

### Recommended Additional Security

⭐ **Consider Implementing:**

1. **Biometric Authentication** (Optional but Recommended)
   ```dart
   import 'package:local_auth/local_auth.dart';
   
   // Add biometric login after first successful password login
   Future<bool> authenticateWithBiometrics() async {
     final auth = LocalAuthentication();
     
     try {
       return await auth.authenticate(
         localizedReason: 'Authenticate to access E-KOLEK',
         options: AuthenticationOptions(
           stickyAuth: true,
           biometricOnly: true,
         ),
       );
     } catch (e) {
       return false;
     }
   }
   ```

2. **Device Fingerprinting**
   ```dart
   import 'package:device_info_plus/device_info_plus.dart';
   
   Future<String> getDeviceFingerprint() async {
     final deviceInfo = DeviceInfoPlugin();
     // Get unique device identifier
     // Send to backend for device tracking
   }
   ```

3. **Session Timeout**
   ```dart
   // Auto-logout after inactivity
   Timer? _sessionTimer;
   
   void resetSessionTimer() {
     _sessionTimer?.cancel();
     _sessionTimer = Timer(Duration(minutes: 30), () {
       // Auto logout
       _authService.logout();
     });
   }
   ```

4. **Failed Login Attempt Limiting**
   ```dart
   int _failedAttempts = 0;
   DateTime? _lockoutUntil;
   
   Future<void> handleFailedLogin() async {
     _failedAttempts++;
     
     if (_failedAttempts >= 3) {
       // Lock account for 5 minutes
       _lockoutUntil = DateTime.now().add(Duration(minutes: 5));
       
       showDialog(
         context: context,
         builder: (context) => AlertDialog(
           title: Text('Too Many Failed Attempts'),
           content: Text('Please wait 5 minutes before trying again.'),
         ),
       );
     }
   }
   ```

---

## 🧪 Testing Your Implementation

### Test Case 1: Successful Login (OTP Disabled)

**Steps:**
1. Enter valid username: `test_user`
2. Enter valid password: `password123`
3. Tap "Login" button

**Expected Result:**
- ✅ Loading indicator appears
- ✅ No navigation to OTP screen
- ✅ Direct navigation to home screen
- ✅ User data loaded in home screen
- ✅ API calls work with saved token

**Backend Response:**
```json
{
  "success": true,
  "message": "Login successful (OTP disabled)",
  "otp_bypassed": true,
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_info": {
    "id": "12345-67890-abcdef",
    "username": "test_user",
    "full_name": "Test User",
    "total_points": 250,
    "status": "approved"
  },
  "family_info": {
    "id": "family-uuid",
    "family_name": "Test Family",
    "family_code": "TSTFAM123",
    "barangay": "Barangay Test"
  }
}
```

### Test Case 2: Invalid Credentials

**Steps:**
1. Enter invalid username: `wrong_user`
2. Enter invalid password: `wrong_pass`
3. Tap "Login"

**Expected Result:**
- ✅ Error message shown: "Invalid username or password"
- ✅ Stay on login screen
- ✅ No token saved

### Test Case 3: API Calls After Login

**Steps:**
1. Login successfully
2. Navigate to profile screen
3. Fetch user data

**Expected Result:**
- ✅ API call includes header: `Authorization: Token abc123...`
- ✅ User data loads successfully
- ✅ Points display correctly

**Test API Call:**
```dart
// Should work after login
final response = await apiService.get('/api/current_user_data/');
// Should return 200 with user data
```

---

## 🐛 Troubleshooting

### Problem 1: "401 Unauthorized" on API Calls

**Symptoms:**
- Login succeeds but subsequent API calls fail with 401

**Solution:**
Check authorization header format:
```dart
// ❌ WRONG (for DRF Token)
'Authorization': 'Bearer $token'

// ✅ CORRECT (for DRF Token when OTP disabled)
'Authorization': 'Token $token'
```

**Debug Code:**
```dart
// Add this to check your header format
final authHeader = await _storage.getAuthorizationHeader();
print('Auth Header: $authHeader');
// Should print: "Token abc123..." NOT "Bearer abc123..."
```

### Problem 2: App Still Shows OTP Screen

**Symptoms:**
- Login redirects to OTP screen even though OTP is disabled

**Solution:**
Check the login response handling:
```dart
// Add debugging
print('Login Response: ${jsonEncode(data)}');
print('OTP Bypassed: ${data['otp_bypassed']}');
print('OTP Sent: ${data['otp_sent']}');

// Verify condition
if (data['otp_bypassed'] == true) {  // Must check for true, not just truthy
  // Go to home
} else if (data['otp_sent'] == true) {
  // Go to OTP screen
}
```

### Problem 3: Token Not Persisting

**Symptoms:**
- User logged out after app restart

**Solution:**
Verify secure storage:
```dart
// Test token persistence
await _storage.saveToken('test_token_123');
final savedToken = await _storage.getToken();
print('Token persisted: ${savedToken == 'test_token_123'}');

// If false, check Flutter Secure Storage setup
```

### Problem 4: Backend Returns "OTP sent" Instead of "OTP bypassed"

**Symptoms:**
- Backend still sending OTP despite disabled flag

**Possible Causes:**
1. Railway environment variable not set correctly
2. Railway app not redeployed after variable change
3. Using wrong backend URL (testing vs production)

**Solution:**
```bash
# Check Railway environment
railway variables --service django
# Should show: OTP_VERIFICATION_ENABLED = False

# Force redeploy
railway up --service django

# Check backend logs
railway logs --service django | grep "OTP"
# Should see: [OTP BYPASS] Skipping OTP for user...
```

---

## 📊 Complete Login Flow Diagram (OTP Disabled)

```
┌─────────────────────────────────────────────────────────┐
│                   User Opens App                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Check Token?   │
            └────┬──────┬────┘
                 │      │
         YES ◄───┘      └───► NO
          │                  │
          ▼                  ▼
    ┌──────────┐      ┌─────────────┐
    │ Home     │      │ Login Screen│
    │ Screen   │      └──────┬──────┘
    └──────────┘             │
                             ▼
                    ┌──────────────────┐
                    │ User Enters:     │
                    │ • Username       │
                    │ • Password       │
                    └────────┬─────────┘
                             │
                             ▼
                    POST /api/login/
                    { username, password }
                             │
                             ▼
                    ┌──────────────────┐
                    │ Backend Validates│
                    │ Credentials      │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
         ✅ SUCCESS                  ❌ FAILED
                │                         │
                ▼                         ▼
    ┌────────────────────┐       ┌──────────────┐
    │ Response:          │       │ Show Error:  │
    │ {                  │       │ "Invalid     │
    │   success: true,   │       │  credentials"│
    │   otp_bypassed:true│       └──────────────┘
    │   token: "abc123"  │
    │   user_info: {...} │
    │ }                  │
    └──────┬─────────────┘
           │
           ▼
    ┌──────────────────┐
    │ Save DRF Token   │
    │ Token Type: 'drf'│
    │ User Data        │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────┐
    │ Navigate to      │
    │ Home Screen      │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────────────┐
    │ User Logged In ✅        │
    │                          │
    │ All API calls use:       │
    │ Authorization:           │
    │ Token abc123...          │
    └──────────────────────────┘
```

---

## ✅ Implementation Checklist

Use this checklist to ensure proper implementation:

### Backend Configuration
- [ ] Verify Railway environment: `OTP_VERIFICATION_ENABLED=False`
- [ ] Check backend logs show: `[OTP BYPASS]` messages
- [ ] Test login endpoint returns `otp_bypassed: true`

### Flutter Code Changes
- [ ] Update `auth_service.dart` to check `otp_bypassed` flag
- [ ] Modify login screen to skip OTP screen when `otp_bypassed: true`
- [ ] Save DRF token (not JWT) when OTP bypassed
- [ ] Set token type to `'drf'` in storage
- [ ] Update authorization header to use `Token` prefix (not `Bearer`)
- [ ] Test all API endpoints with new token format

### Testing
- [ ] Test successful login flow (no OTP screen)
- [ ] Test invalid credentials show error
- [ ] Test API calls work after login
- [ ] Test token persists after app restart
- [ ] Test logout clears token correctly

### Security
- [ ] Verify token stored in secure storage
- [ ] Implement session timeout (optional)
- [ ] Add biometric authentication (optional)
- [ ] Add device fingerprinting (optional)

### User Experience
- [ ] Show loading indicator during login
- [ ] Display success message on login
- [ ] Show clear error messages for failures
- [ ] Smooth transition to home screen

---

## 🎓 Key Takeaways

### What Changed?
1. **Before (OTP Enabled)**: 2-step login (credentials → OTP verification)
2. **Now (OTP Disabled)**: 1-step login (credentials → immediate access)

### What Your App Must Do?
1. Check `otp_bypassed` flag in login response
2. Skip OTP screen when flag is `true`
3. Use DRF Token with `Token` header prefix
4. Save token type as `'drf'`

### What Stays the Same?
1. Username/password validation
2. Secure token storage
3. API authentication requirement
4. Backend security validations

### Security Trade-offs
- **Lost**: SMS-based two-factor authentication
- **Kept**: Password authentication, token-based sessions, backend validations
- **Recommended**: Add biometric authentication, device tracking, session timeouts

---

## 📞 Support

**If you encounter issues:**

1. **Check Backend Logs**
   ```bash
   railway logs --service django | grep "login"
   ```

2. **Check Backend Response**
   ```dart
   print('Login Response: ${jsonEncode(data)}');
   ```

3. **Verify Token Format**
   ```dart
   final header = await storage.getAuthorizationHeader();
   print('Auth Header: $header');  // Should be "Token abc..."
   ```

4. **Test API Endpoint Directly**
   ```bash
   curl -X POST https://your-app.railway.app/api/login/ \
     -H "Content-Type: application/json" \
     -d '{"username":"test_user","password":"test_password"}'
   ```

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Status**: Production Implementation Ready ✅

**Next Steps**: Copy the code examples above into your Flutter app and test the login flow!
