# 🚀 Complete Flutter Mobile App Implementation Guide (OTP Disabled)

**Status:** ✅ Backend Ready | Token Authentication Fixed | OTP Bypass Active  
**Last Updated:** January 21, 2026  
**Critical:** Read this entire guide before implementing!

---

## 📊 System Architecture Overview

### Backend Configuration
- **Django 5.2.4** + Django REST Framework
- **Authentication:** DRF Token (when OTP disabled) or JWT (when OTP enabled)
- **OTP Status:** DISABLED in Railway (`OTP_VERIFICATION_ENABLED=False`)
- **CORS:** Enabled for mobile app access
- **All Endpoints:** Support both Token and JWT authentication

### Authentication Flow (OTP Disabled)
```
User Login → Username + Password → Immediate Token → Access All Endpoints
```

**No OTP Screen Needed!**

---

## 🔑 Critical Backend Changes Applied

### 1. REST Framework Settings (Fixed)
```python
# eko/settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT (OTP enabled)
        'rest_framework.authentication.TokenAuthentication',  # ✅ DRF Token (OTP disabled)
        'eko.authentication.CsrfExemptSessionAuthentication',
    ],
}
```

### 2. Logout Endpoint (Fixed)
```python
# mobilelogin/auth_views.py
@authentication_classes([JWTAuthentication, TokenAuthentication])  # ✅ Now supports both
def logout_view(request):
    # Detects token type and handles appropriately
    if isinstance(request.auth, Token):
        request.auth.delete()  # DRF Token
    else:
        token.blacklist()  # JWT Token
```

### 3. Token Validation (Fixed)
```python
# mobilelogin/auth_views.py
@authentication_classes([JWTAuthentication, TokenAuthentication])  # ✅ Now supports both
def validate_token_view(request):
    token_type = 'Token' if isinstance(request.auth, Token) else 'Bearer'
    # Returns correct token type
```

---

## 📱 Flutter App Implementation

### Step 1: API Configuration

```dart
// lib/config/api_config.dart
class ApiConfig {
  // ⚠️ IMPORTANT: Update with your Railway URL
  static const String baseUrl = 'https://your-app.railway.app';
  
  // Authentication Endpoints
  static const String login = '/api/login/';
  static const String qrLogin = '/api/qr-login/';
  static const String logout = '/api/logout/';
  static const String validateToken = '/api/validate-token/';
  
  // User Data Endpoints
  static const String currentPoints = '/api/current_points/';
  static const String currentUserData = '/api/current_user_data/';
  static const String familyMembers = '/api/family_members/';
  
  // Schedule Endpoints
  static const String schedule = '/api/schedule/';
  static const String allSchedules = '/api/schedule/all/';
  static const String todaysSchedule = '/api/schedule/today/';
  
  // Game Endpoints
  static const String gameConfigurations = '/api/game/configurations/';
  static const String quizCooldown = '/api/game/cooldown/quiz/';
  static const String dragdropCooldown = '/api/game/cooldown/dragdrop/';
  
  // Notification Endpoints
  static const String notifications = '/api/notifications/';
  static const String unreadCount = '/api/notifications/unread-count/';
  
  // Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
}
```

### Step 2: Authentication Service

```dart
// lib/services/auth_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'storage_service.dart';

class AuthService {
  final StorageService _storage = StorageService();

  /// Login with username and password (OTP Disabled Mode)
  Future<LoginResult> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.login}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username.trim(),
          'password': password,
        }),
      ).timeout(ApiConfig.connectionTimeout);

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        
        // ✅ Check if OTP was bypassed (OTP disabled)
        if (data['otp_bypassed'] == true) {
          // Login complete in ONE STEP!
          await _storage.saveToken(data['token']);
          await _storage.saveTokenType('token');  // DRF Token
          
          if (data['user_info'] != null) {
            await _storage.saveUserData(data['user_info']);
            await _storage.saveUserId(data['user_info']['id']);
          }
          
          if (data['family_info'] != null) {
            await _storage.saveFamilyData(data['family_info']);
          }
          
          return LoginResult(
            success: true,
            otpRequired: false,  // ✅ No OTP needed!
            message: data['message'] ?? 'Login successful',
          );
        }
        
        // If OTP is enabled (for backward compatibility)
        else if (data['otp_sent'] == true) {
          return LoginResult(
            success: true,
            otpRequired: true,
            userId: data['user_id'],
            message: 'OTP sent to your phone',
          );
        }
      }

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

  /// QR Code Login (OTP Disabled Mode)
  Future<LoginResult> qrLogin(String qrCode) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.qrLogin}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'qr_code': qrCode.trim()}),
      ).timeout(ApiConfig.connectionTimeout);

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        if (data['otp_bypassed'] == true) {
          await _storage.saveToken(data['token']);
          await _storage.saveTokenType('token');
          
          if (data['user_info'] != null) {
            await _storage.saveUserData(data['user_info']);
          }
          
          return LoginResult(
            success: true,
            otpRequired: false,
            message: 'QR login successful',
          );
        }
      }

      return LoginResult(
        success: false,
        message: data['message'] ?? 'QR login failed',
      );

    } catch (e) {
      return LoginResult(
        success: false,
        message: 'Connection error: ${e.toString()}',
      );
    }
  }

  /// Validate current token
  Future<bool> validateToken() async {
    try {
      final authHeader = await _storage.getAuthorizationHeader();
      if (authHeader == null) return false;

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.validateToken}'),
        headers: {'Authorization': authHeader},
      ).timeout(ApiConfig.connectionTimeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['success'] == true;
      }
      
      return false;
    } catch (e) {
      return false;
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      final authHeader = await _storage.getAuthorizationHeader();

      if (authHeader != null) {
        await http.post(
          Uri.parse('${ApiConfig.baseUrl}${ApiConfig.logout}'),
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
        ).timeout(ApiConfig.connectionTimeout);
      }
    } catch (e) {
      // Ignore logout errors
    } finally {
      await _storage.clearAll();
    }
  }

  /// Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await _storage.getToken();
    return token != null && token.isNotEmpty;
  }
}

/// Login result model
class LoginResult {
  final bool success;
  final bool otpRequired;
  final String? userId;
  final String message;
  final String? errorCode;

  LoginResult({
    required this.success,
    this.otpRequired = false,
    this.userId,
    required this.message,
    this.errorCode,
  });
}
```

### Step 3: Storage Service

```dart
// lib/services/storage_service.dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:convert';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  final _secureStorage = const FlutterSecureStorage();

  // ==================== TOKEN MANAGEMENT ====================
  
  /// Save authentication token
  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: 'auth_token', value: token);
  }

  /// Get saved authentication token
  Future<String?> getToken() async {
    return await _secureStorage.read(key: 'auth_token');
  }

  /// Save token type ('token' for DRF Token, 'bearer' for JWT)
  Future<void> saveTokenType(String type) async {
    await _secureStorage.write(key: 'token_type', value: type);
  }

  /// Get token type
  Future<String?> getTokenType() async {
    return await _secureStorage.read(key: 'token_type');
  }

  /// Get authorization header for API requests
  Future<String?> getAuthorizationHeader() async {
    final token = await getToken();
    if (token == null) return null;
    
    final tokenType = await getTokenType();
    
    // ⚠️ CRITICAL: Different header formats
    if (tokenType == 'bearer') {
      return 'Bearer $token';  // JWT Token
    } else {
      return 'Token $token';  // ✅ DRF Token (OTP disabled)
    }
  }

  /// Clear all authentication data
  Future<void> clearAuthData() async {
    await _secureStorage.delete(key: 'auth_token');
    await _secureStorage.delete(key: 'token_type');
    await _secureStorage.delete(key: 'user_id');
    await _secureStorage.delete(key: 'user_data');
    await _secureStorage.delete(key: 'family_data');
  }

  // ==================== USER DATA ====================

  /// Save user data
  Future<void> saveUserData(Map<String, dynamic> userData) async {
    await _secureStorage.write(
      key: 'user_data',
      value: jsonEncode(userData),
    );
  }

  /// Get user data
  Future<Map<String, dynamic>?> getUserData() async {
    final data = await _secureStorage.read(key: 'user_data');
    if (data == null) return null;
    return jsonDecode(data);
  }

  /// Save user ID
  Future<void> saveUserId(String userId) async {
    await _secureStorage.write(key: 'user_id', value: userId);
  }

  /// Get user ID
  Future<String?> getUserId() async {
    return await _secureStorage.read(key: 'user_id');
  }

  /// Save family data
  Future<void> saveFamilyData(Map<String, dynamic> familyData) async {
    await _secureStorage.write(
      key: 'family_data',
      value: jsonEncode(familyData),
    );
  }

  /// Get family data
  Future<Map<String, dynamic>?> getFamilyData() async {
    final data = await _secureStorage.read(key: 'family_data');
    if (data == null) return null;
    return jsonDecode(data);
  }

  /// Clear all data
  Future<void> clearAll() async {
    await clearAuthData();
  }
}
```

### Step 4: API Service (For Protected Endpoints)

```dart
// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'storage_service.dart';

class ApiService {
  final StorageService _storage = StorageService();

  /// Make authenticated GET request
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

      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: {
          'Authorization': authHeader,  // ✅ Automatically uses correct format
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

  /// Make authenticated POST request
  Future<ApiResponse> post(String endpoint, Map<String, dynamic> data) async {
    try {
      final authHeader = await _storage.getAuthorizationHeader();
      if (authHeader == null) {
        return ApiResponse(
          success: false,
          message: 'Not authenticated',
          statusCode: 401,
        );
      }

      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: {
          'Authorization': authHeader,
          'Content-Type': 'application/json',
        },
        body: jsonEncode(data),
      ).timeout(ApiConfig.connectionTimeout);

      return _handleResponse(response);
    } catch (e) {
      return ApiResponse(
        success: false,
        message: 'Network error: ${e.toString()}',
      );
    }
  }

  /// Handle API response
  ApiResponse _handleResponse(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      
      return ApiResponse(
        success: response.statusCode >= 200 && response.statusCode < 300,
        message: data['message'] ?? '',
        data: data,
        statusCode: response.statusCode,
      );
    } catch (e) {
      return ApiResponse(
        success: false,
        message: 'Invalid response format',
        statusCode: response.statusCode,
      );
    }
  }
}

/// API Response model
class ApiResponse {
  final bool success;
  final String message;
  final dynamic data;
  final int? statusCode;

  ApiResponse({
    required this.success,
    required this.message,
    this.data,
    this.statusCode,
  });
}
```

### Step 5: Login Screen

```dart
// lib/screens/auth/login_screen.dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import '../home/home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _authService = AuthService();
  
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

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
        // ✅ OTP is disabled - go directly to home
        // No OTP screen needed!
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeScreen()),
        );
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Welcome back!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Icon(
                    Icons.recycling,
                    size: 100,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(height: 24),
                  
                  Text(
                    'E-KOLEK',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 48),
                  
                  // Username field
                  TextFormField(
                    controller: _usernameController,
                    decoration: InputDecoration(
                      labelText: 'Username',
                      prefixIcon: const Icon(Icons.person),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return 'Please enter your username';
                      }
                      return null;
                    },
                    textInputAction: TextInputAction.next,
                  ),
                  const SizedBox(height: 16),
                  
                  // Password field
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword ? Icons.visibility : Icons.visibility_off,
                        ),
                        onPressed: () {
                          setState(() => _obscurePassword = !_obscurePassword);
                        },
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter your password';
                      }
                      return null;
                    },
                    onFieldSubmitted: (_) => _handleLogin(),
                  ),
                  const SizedBox(height: 24),
                  
                  // Login button
                  ElevatedButton(
                    onPressed: _isLoading ? null : _handleLogin,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text(
                            'Login',
                            style: TextStyle(fontSize: 16),
                          ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
```

---

## 🧪 Testing Your Implementation

### Test 1: Backend Endpoint Test

```bash
# Update the test script with your Railway URL and credentials
python test_flutter_api.py
```

Should show:
```
✓ Login Endpoint: 200
✓ OTP is DISABLED - Single-step login ✓
✓ DRF Token received: abc123...
✓ Get Current User Data: 200
✓ Get Current Points: 200
🎉 ALL TESTS PASSED - READY FOR PRESENTATION!
```

### Test 2: Manual cURL Test

```bash
# Test login
curl -X POST https://your-app.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}'

# Should return:
{
  "success": true,
  "otp_bypassed": true,
  "token": "abc123...",
  "user_info": {...}
}

# Test protected endpoint
curl -X GET https://your-app.railway.app/api/current_user_data/ \
  -H "Authorization: Token abc123..."

# Should return user data
```

### Test 3: Flutter App Test

1. **Update API Base URL** in `api_config.dart`
2. **Run the app:** `flutter run`
3. **Login** with valid credentials
4. **Verify:**
   - ✅ No OTP screen appears
   - ✅ Direct navigation to home screen
   - ✅ User data loads correctly
   - ✅ All API calls work

---

## 🔍 Troubleshooting

### Problem: "401 Unauthorized" on API Calls

**Solution:** Check authorization header format

```dart
// ❌ WRONG
headers: {'Authorization': 'Bearer $token'}

// ✅ CORRECT (when OTP disabled)
headers: {'Authorization': 'Token $token'}

// ✅ BEST (auto-detect)
final authHeader = await _storage.getAuthorizationHeader();
headers: {'Authorization': authHeader}
```

### Problem: App Still Shows OTP Screen

**Solution:** Check login response handling

```dart
if (data['otp_bypassed'] == true) {  // ✅ Must check for true
  // Skip OTP - go to home
}
```

### Problem: Token Not Persisting

**Solution:** Verify secure storage

```dart
await _storage.saveToken(token);
await _storage.saveTokenType('token');  // Must save type!
```

---

## ✅ Deployment Checklist

- [x] Backend: TokenAuthentication added to REST_FRAMEWORK
- [x] Backend: CORS enabled for mobile app
- [x] Backend: Logout endpoint supports Token authentication
- [x] Backend: Validate endpoint supports Token authentication
- [x] Backend: All protected endpoints support both auth types
- [x] Railway: OTP_VERIFICATION_ENABLED = False
- [ ] Flutter: Update API base URL
- [ ] Flutter: Implement authentication service
- [ ] Flutter: Implement storage service
- [ ] Flutter: Implement API service
- [ ] Flutter: Test login flow
- [ ] Flutter: Test all API endpoints
- [ ] Flutter: Prepare for presentation

---

## 📊 API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/login/` | POST | None | Login (returns token) |
| `/api/logout/` | POST | Token/JWT | Logout |
| `/api/validate-token/` | GET | Token/JWT | Validate token |
| `/api/current_user_data/` | GET | Token/JWT | Get user data |
| `/api/current_points/` | GET | Token/JWT | Get points |
| `/api/family_members/` | GET | Token/JWT | Get family |
| `/api/schedule/` | GET | Token/JWT | Get schedule |
| `/api/game/configurations/` | GET | Token/JWT | Get game config |
| `/api/notifications/` | GET | Token/JWT | Get notifications |

All protected endpoints support **both** Token and JWT authentication!

---

## 🎉 Success Criteria

Your implementation is ready when:
- ✅ Backend test script shows 100% pass rate
- ✅ Flutter app can login without OTP
- ✅ All screens load data from backend
- ✅ No authentication errors
- ✅ Token persists after app restart

**Good luck with your presentation!** 🚀

---

**Last Updated:** January 21, 2026  
**Status:** ✅ PRODUCTION READY  
**Backend:** Django 5.2.4 + DRF on Railway  
**Frontend:** Flutter Mobile App
