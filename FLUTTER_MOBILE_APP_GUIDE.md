# E-KOLEK Flutter Mobile App Development Guide

**Complete Implementation Guide for Flutter Mobile Application**  
*Production-Ready Documentation | Version 1.0 | January 2026*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Architecture Overview](#architecture-overview)
4. [Authentication Implementation](#authentication-implementation)
5. [API Service Layer](#api-service-layer)
6. [State Management](#state-management)
7. [All API Endpoints](#all-api-endpoints)
8. [Error Handling](#error-handling)
9. [Security Best Practices](#security-best-practices)
10. [Testing Guide](#testing-guide)
11. [Deployment Checklist](#deployment-checklist)

---

## Project Overview

### What is E-KOLEK?

E-KOLEK is a waste management and gamification system that allows:
- **Families** to earn points by properly disposing of garbage
- **Users** to track garbage collection schedules
- **Communities** to compete in eco-friendly activities
- **Players** to earn rewards through quiz and drag-drop games

### Backend Architecture

- **Platform**: Django 5.2.4 + Django REST Framework
- **Authentication**: Dual-mode (JWT tokens when OTP enabled, DRF tokens when OTP disabled)
- **API Base URL**: `https://your-app.railway.app` (replace with your Railway URL)
- **Current Config**: ⚠️ **OTP verification is DISABLED** - Users login directly without SMS OTP

### 🚨 IMPORTANT: OTP Is Already Disabled

**Current Production State:**
- ✅ Backend: `OTP_VERIFICATION_ENABLED = False` (configured in Railway)
- ✅ Mobile Login: Single-step authentication (username + password only)
- ✅ No SMS OTP sent
- ✅ Response includes `otp_bypassed: true` flag

**What This Means for Your Flutter App:**
1. Users will **NOT** receive OTP codes via SMS
2. Login completes in **ONE STEP** (no OTP verification screen needed)
3. App must check `otp_bypassed` flag in login response
4. Skip OTP verification screen when `otp_bypassed: true`
5. Use DRF Token authentication (not JWT)

---

## Prerequisites & Setup

### Required Tools

1. **Flutter SDK**: Version 3.16.0 or higher
   ```bash
   flutter --version
   ```

2. **Dart SDK**: Version 3.2.0 or higher

3. **IDE**: Android Studio / VS Code with Flutter extensions

4. **Required Flutter Packages**:
   ```yaml
   dependencies:
     flutter:
       sdk: flutter
     
     # HTTP & API
     http: ^1.2.0
     dio: ^5.4.0  # Alternative to http, more features
     
     # State Management
     provider: ^6.1.1
     get: ^4.6.6  # Alternative state management
     
     # Local Storage
     shared_preferences: ^2.2.2
     flutter_secure_storage: ^9.0.0
     
     # UI Components
     flutter_spinkit: ^5.2.0
     cached_network_image: ^3.3.1
     pull_to_refresh: ^2.0.0
     
     # QR Code
     qr_code_scanner: ^1.0.1
     mobile_scanner: ^3.5.5  # Modern QR scanner
     
     # Biometric Auth
     local_auth: ^2.1.8
     
     # Utilities
     intl: ^0.19.0
     logger: ^2.0.2
   ```

### Project Structure

```
lib/
├── main.dart
├── config/
│   ├── api_config.dart          # API base URLs and endpoints
│   └── app_config.dart          # App-wide configuration
├── models/
│   ├── user.dart                # User model
│   ├── family.dart              # Family model
│   ├── schedule.dart            # Garbage schedule model
│   └── notification.dart        # Notification model
├── services/
│   ├── api_service.dart         # Base API service
│   ├── auth_service.dart        # Authentication service
│   ├── user_service.dart        # User data service
│   ├── schedule_service.dart    # Schedule service
│   ├── game_service.dart        # Game service
│   └── storage_service.dart     # Local storage service
├── providers/
│   ├── auth_provider.dart       # Authentication state
│   ├── user_provider.dart       # User state
│   └── theme_provider.dart      # Theme state
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart
│   │   ├── qr_login_screen.dart
│   │   └── otp_verify_screen.dart
│   ├── home/
│   │   └── home_screen.dart
│   ├── profile/
│   │   └── profile_screen.dart
│   └── schedule/
│       └── schedule_screen.dart
├── widgets/
│   ├── common/
│   │   ├── loading_indicator.dart
│   │   └── error_dialog.dart
│   └── custom_button.dart
└── utils/
    ├── constants.dart
    ├── validators.dart
    └── helpers.dart
```

---

## Architecture Overview

### Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile App Launch                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Check Saved    │
            │ Token Exists?  │
            └────┬──────┬────┘
                 │      │
        YES ◄────┘      └────► NO
         │                    │
         ▼                    ▼
┌─────────────────┐   ┌─────────────────┐
│ Validate Token  │   │ Show Login      │
│ with Backend    │   │ Screen          │
└────┬───────┬────┘   └────────┬────────┘
     │       │                  │
VALID│  INVALID                 │
     │       │                  │
     ▼       ▼                  ▼
  ┌─────┐ ┌─────┐      ┌───────────────┐
  │HOME │ │LOGIN│      │ User Enters   │
  └─────┘ └─────┘      │ Credentials   │
                        └───────┬───────┘
                                │
                                ▼
                        POST /api/login/
                                │
                    ┌───────────┴───────────┐
                    │                       │
             otp_bypassed=true      otp_sent=true
                    │                       │
                    ▼                       ▼
           ┌─────────────────┐    ┌─────────────────┐
           │ Save DRF Token  │    │ Show OTP Screen │
           │ Navigate Home   │    │ User Enters OTP │
           └─────────────────┘    └────────┬────────┘
                                            │
                                            ▼
                                  POST /api/login/verify-otp/
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │ Save JWT Token  │
                                   │ Navigate Home   │
                                   └─────────────────┘
```

---

## Authentication Implementation

### Step 1: API Configuration

**File**: `lib/config/api_config.dart`

```dart
class ApiConfig {
  // ⚠️ IMPORTANT: Replace with your Railway URL
  static const String baseUrl = 'https://your-app.railway.app';
  
  // Authentication Endpoints
  static const String login = '/api/login/';
  static const String qrLogin = '/api/qr-login/';
  static const String verifyOtp = '/api/login/verify-otp/';
  static const String logout = '/api/logout/';
  static const String refreshToken = '/api/refresh-token/';
  static const String validateToken = '/api/validate-token/';
  
  // User Data Endpoints
  static const String currentPoints = '/api/current_points/';
  static const String currentUserData = '/api/current_user_data/';
  static const String familyMembers = '/api/family_members/';
  static const String updatePoints = '/api/update_points/';
  
  // Schedule Endpoints
  static const String schedule = '/api/schedule/';
  static const String allSchedules = '/api/schedule/all/';
  static const String todaysSchedule = '/api/schedule/today/';
  static String scheduleByBarangay(String barangayId) => 
      '/api/schedule/barangay/$barangayId/';
  
  // Game Endpoints
  static const String gameConfigurations = '/api/game/configurations/';
  static String gameCooldown(String gameType) => '/api/game/cooldown/$gameType/';
  static const String quizCooldown = '/api/game/cooldown/quiz/';
  static const String dragdropCooldown = '/api/game/cooldown/dragdrop/';
  
  // Notification Endpoints
  static const String notifications = '/api/notifications/';
  static const String markNotificationsViewed = '/api/notifications/mark-viewed/';
  static String markNotificationRead(String notificationId) => 
      '/api/notifications/$notificationId/mark-read/';
  static const String unreadCount = '/api/notifications/unread-count/';
  
  // Biometric Endpoints
  static const String biometricRegister = '/api/biometric/register/';
  static const String biometricLoginInit = '/api/biometric/login/init/';
  static const String biometricLoginVerify = '/api/biometric/login/verify/';
  static const String biometricDevices = '/api/biometric/devices/';
  static String biometricRevoke(String deviceId) => 
      '/api/biometric/devices/$deviceId/revoke/';
  static String biometricTrust(String deviceId) => 
      '/api/biometric/devices/$deviceId/trust/';
  static const String biometricHistory = '/api/biometric/history/';
  
  // Request Timeouts
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
}
```

### Step 2: Storage Service

**File**: `lib/services/storage_service.dart`

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  // Secure storage for sensitive data (tokens)
  final _secureStorage = const FlutterSecureStorage();
  
  // Regular storage for non-sensitive data
  SharedPreferences? _prefs;

  // Initialize storage
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
  }

  // ==================== TOKEN MANAGEMENT ====================
  
  /// Save authentication token (works for both JWT and DRF Token)
  Future<void> saveToken(String token) async {
    await _secureStorage.write(key: 'auth_token', value: token);
  }

  /// Get saved authentication token
  Future<String?> getToken() async {
    return await _secureStorage.read(key: 'auth_token');
  }

  /// Save token type ('jwt' or 'drf')
  Future<void> saveTokenType(String type) async {
    await _secureStorage.write(key: 'token_type', value: type);
  }

  /// Get token type
  Future<String?> getTokenType() async {
    return await _secureStorage.read(key: 'token_type');
  }

  /// Save refresh token (only for JWT)
  Future<void> saveRefreshToken(String refreshToken) async {
    await _secureStorage.write(key: 'refresh_token', value: refreshToken);
  }

  /// Get refresh token
  Future<String?> getRefreshToken() async {
    return await _secureStorage.read(key: 'refresh_token');
  }

  /// Get authorization header format
  Future<String?> getAuthorizationHeader() async {
    final token = await getToken();
    if (token == null) return null;
    
    final tokenType = await getTokenType();
    if (tokenType == 'jwt') {
      return 'Bearer $token';
    } else {
      // DRF Token (OTP bypassed)
      return 'Token $token';
    }
  }

  /// Clear all authentication data
  Future<void> clearAuthData() async {
    await _secureStorage.delete(key: 'auth_token');
    await _secureStorage.delete(key: 'token_type');
    await _secureStorage.delete(key: 'refresh_token');
    await _secureStorage.delete(key: 'user_id');
  }

  // ==================== USER DATA ====================

  /// Save user data to secure storage
  Future<void> saveUserData(Map<String, dynamic> userData) async {
    await _secureStorage.write(
      key: 'user_data',
      value: jsonEncode(userData),
    );
  }

  /// Get user data from secure storage
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

  // ==================== APP PREFERENCES ====================

  /// Check if user has completed onboarding
  bool hasCompletedOnboarding() {
    return _prefs?.getBool('onboarding_complete') ?? false;
  }

  /// Mark onboarding as complete
  Future<void> setOnboardingComplete() async {
    await _prefs?.setBool('onboarding_complete', true);
  }

  /// Save theme preference
  Future<void> saveThemeMode(bool isDark) async {
    await _prefs?.setBool('is_dark_mode', isDark);
  }

  /// Get theme preference
  bool isDarkMode() {
    return _prefs?.getBool('is_dark_mode') ?? false;
  }

  /// Check if this is first app launch
  bool isFirstLaunch() {
    return _prefs?.getBool('first_launch') ?? true;
  }

  /// Mark app as launched
  Future<void> setAppLaunched() async {
    await _prefs?.setBool('first_launch', false);
  }

  // ==================== CACHE MANAGEMENT ====================

  /// Save cached data with timestamp
  Future<void> saveCache(String key, dynamic data, {Duration? ttl}) async {
    final cacheData = {
      'data': data,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'ttl': ttl?.inMilliseconds,
    };
    await _prefs?.setString('cache_$key', jsonEncode(cacheData));
  }

  /// Get cached data if not expired
  dynamic getCache(String key) {
    final cached = _prefs?.getString('cache_$key');
    if (cached == null) return null;

    try {
      final cacheData = jsonDecode(cached);
      final timestamp = cacheData['timestamp'] as int;
      final ttl = cacheData['ttl'] as int?;

      if (ttl != null) {
        final expiryTime = timestamp + ttl;
        if (DateTime.now().millisecondsSinceEpoch > expiryTime) {
          // Cache expired
          _prefs?.remove('cache_$key');
          return null;
        }
      }

      return cacheData['data'];
    } catch (e) {
      return null;
    }
  }

  /// Clear all cache
  Future<void> clearCache() async {
    final keys = _prefs?.getKeys() ?? {};
    for (var key in keys) {
      if (key.startsWith('cache_')) {
        await _prefs?.remove(key);
      }
    }
  }

  /// Clear all data (logout)
  Future<void> clearAll() async {
    await clearAuthData();
    await clearCache();
  }
}
```

### Step 3: Authentication Service

**File**: `lib/services/auth_service.dart`

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import 'storage_service.dart';

class AuthService {
  final StorageService _storage = StorageService();

  /// Login with username and password
  /// Returns LoginResult with success status and message
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
        // Check if OTP was bypassed
        if (data['otp_bypassed'] == true) {
          // OTP DISABLED: Login complete in one step
          await _handleDirectLogin(data);
          return LoginResult(
            success: true,
            otpRequired: false,
            message: data['message'] ?? 'Login successful',
          );
        } else if (data['otp_sent'] == true) {
          // OTP ENABLED: Need to verify OTP
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

  /// QR Code Login
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
          // Direct login without OTP
          await _handleDirectLogin(data);
          return LoginResult(
            success: true,
            otpRequired: false,
            message: data['message'] ?? 'QR login successful',
          );
        } else if (data['otp_sent'] == true) {
          // OTP required
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
        message: data['message'] ?? 'QR login failed',
        errorCode: data['error_code'],
      );

    } catch (e) {
      return LoginResult(
        success: false,
        message: 'Connection error: ${e.toString()}',
      );
    }
  }

  /// Verify OTP code
  Future<LoginResult> verifyOtp(String userId, String otp) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.verifyOtp}'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'otp': otp.trim(),
        }),
      ).timeout(ApiConfig.connectionTimeout);

      final data = jsonDecode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        // Save JWT tokens
        await _storage.saveToken(data['access_token']);
        await _storage.saveTokenType('jwt');
        await _storage.saveRefreshToken(data['refresh_token']);
        
        // Save user data
        if (data['user_info'] != null) {
          await _storage.saveUserData(data['user_info']);
          await _storage.saveUserId(data['user_info']['id']);
        }

        return LoginResult(
          success: true,
          otpRequired: false,
          message: 'OTP verified successfully',
        );
      }

      return LoginResult(
        success: false,
        message: data['message'] ?? 'Invalid OTP',
        errorCode: data['error_code'],
      );

    } catch (e) {
      return LoginResult(
        success: false,
        message: 'Connection error: ${e.toString()}',
      );
    }
  }

  /// Handle direct login (OTP bypassed)
  Future<void> _handleDirectLogin(Map<String, dynamic> data) async {
    // Save DRF Token
    await _storage.saveToken(data['token']);
    await _storage.saveTokenType('drf');
    
    // Save user data
    if (data['user_info'] != null) {
      await _storage.saveUserData(data['user_info']);
      await _storage.saveUserId(data['user_info']['id']);
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

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Logout
  Future<void> logout() async {
    try {
      final authHeader = await _storage.getAuthorizationHeader();
      final refreshToken = await _storage.getRefreshToken();

      if (authHeader != null) {
        await http.post(
          Uri.parse('${ApiConfig.baseUrl}${ApiConfig.logout}'),
          headers: {
            'Authorization': authHeader,
            'Content-Type': 'application/json',
          },
          body: jsonEncode({
            if (refreshToken != null) 'refresh_token': refreshToken,
          }),
        ).timeout(ApiConfig.connectionTimeout);
      }
    } catch (e) {
      // Ignore logout errors
    } finally {
      // Always clear local data
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

### Step 4: Login Screen

**File**: `lib/screens/auth/login_screen.dart`

```dart
import 'package:flutter/material.dart';
import '../../services/auth_service.dart';
import 'otp_verify_screen.dart';
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
        if (result.otpRequired) {
          // Navigate to OTP verification screen
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(
              builder: (context) => OtpVerifyScreen(
                userId: result.userId!,
                phoneNumber: 'your phone',  // You can get this from result if needed
              ),
            ),
          );
        } else {
          // Direct login success (OTP bypassed)
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (context) => const HomeScreen()),
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
                  // Logo
                  Icon(
                    Icons.recycling,
                    size: 100,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(height: 24),
                  
                  // Title
                  Text(
                    'E-KOLEK',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Waste Management System',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.grey,
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
                      if (value.length < 6) {
                        return 'Password must be at least 6 characters';
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
                  const SizedBox(height: 16),
                  
                  // QR Login button
                  OutlinedButton.icon(
                    onPressed: _isLoading ? null : () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const QrLoginScreen(),
                        ),
                      );
                    },
                    icon: const Icon(Icons.qr_code_scanner),
                    label: const Text('Login with QR Code'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
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

### Step 5: OTP Verification Screen

**File**: `lib/screens/auth/otp_verify_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'dart:async';
import '../../services/auth_service.dart';
import '../home/home_screen.dart';

class OtpVerifyScreen extends StatefulWidget {
  final String userId;
  final String phoneNumber;

  const OtpVerifyScreen({
    Key? key,
    required this.userId,
    required this.phoneNumber,
  }) : super(key: key);

  @override
  State<OtpVerifyScreen> createState() => _OtpVerifyScreenState();
}

class _OtpVerifyScreenState extends State<OtpVerifyScreen> {
  final _otpController = TextEditingController();
  final _authService = AuthService();
  
  bool _isLoading = false;
  int _resendCountdown = 60;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  @override
  void dispose() {
    _otpController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _startResendTimer() {
    _resendCountdown = 60;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_resendCountdown > 0) {
        setState(() => _resendCountdown--);
      } else {
        timer.cancel();
      }
    });
  }

  Future<void> _verifyOtp() async {
    if (_otpController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter OTP code')),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final result = await _authService.verifyOtp(
        widget.userId,
        _otpController.text,
      );

      if (!mounted) return;

      if (result.success) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const HomeScreen()),
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
      appBar: AppBar(
        title: const Text('Verify OTP'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 32),
              Icon(
                Icons.sms,
                size: 80,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 24),
              Text(
                'Enter Verification Code',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                'We sent a code to ${widget.phoneNumber}',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey[600]),
              ),
              const SizedBox(height: 48),
              
              // OTP Input
              TextField(
                controller: _otpController,
                keyboardType: TextInputType.number,
                maxLength: 6,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 24,
                  letterSpacing: 8,
                  fontWeight: FontWeight.bold,
                ),
                decoration: InputDecoration(
                  hintText: '------',
                  counterText: '',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onSubmitted: (_) => _verifyOtp(),
              ),
              const SizedBox(height: 24),
              
              // Verify Button
              ElevatedButton(
                onPressed: _isLoading ? null : _verifyOtp,
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
                    : const Text('Verify OTP'),
              ),
              const SizedBox(height: 16),
              
              // Resend OTP
              TextButton(
                onPressed: _resendCountdown == 0 ? () {
                  // TODO: Implement resend OTP
                  _startResendTimer();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('OTP resent')),
                  );
                } : null,
                child: Text(
                  _resendCountdown > 0
                      ? 'Resend OTP in $_resendCountdown seconds'
                      : 'Resend OTP',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## API Service Layer

### Complete API Service Implementation

**File**: `lib/services/api_service.dart`

```dart
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
          'Authorization': authHeader,
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

---

## All API Endpoints

### User Service Implementation

**File**: `lib/services/user_service.dart`

```dart
import 'api_service.dart';
import '../config/api_config.dart';
import '../models/user.dart';

class UserService {
  final ApiService _api = ApiService();

  /// Get current user points
  Future<ApiResponse> getCurrentPoints() async {
    return await _api.get(ApiConfig.currentPoints);
  }

  /// Get current user data
  Future<ApiResponse> getCurrentUserData() async {
    return await _api.get(ApiConfig.currentUserData);
  }

  /// Get family members
  Future<ApiResponse> getFamilyMembers() async {
    return await _api.get(ApiConfig.familyMembers);
  }

  /// Update user points
  Future<ApiResponse> updatePoints(int points) async {
    return await _api.post(ApiConfig.updatePoints, {
      'total_points': points,
    });
  }
}
```

### Schedule Service Implementation

**File**: `lib/services/schedule_service.dart`

```dart
import 'api_service.dart';
import '../config/api_config.dart';

class ScheduleService {
  final ApiService _api = ApiService();

  /// Get garbage collection schedule for user's barangay
  Future<ApiResponse> getSchedule() async {
    return await _api.get(ApiConfig.schedule);
  }

  /// Get all schedules across all barangays
  Future<ApiResponse> getAllSchedules() async {
    return await _api.get(ApiConfig.allSchedules);
  }

  /// Get today's schedule
  Future<ApiResponse> getTodaysSchedule() async {
    return await _api.get(ApiConfig.todaysSchedule);
  }

  /// Get schedule by specific barangay
  Future<ApiResponse> getScheduleByBarangay(String barangayId) async {
    return await _api.get(ApiConfig.scheduleByBarangay(barangayId));
  }
}
```

### Game Service Implementation

**File**: `lib/services/game_service.dart`

```dart
import 'api_service.dart';
import '../config/api_config.dart';

class GameService {
  final ApiService _api = ApiService();

  /// Get all game configurations
  Future<ApiResponse> getGameConfigurations() async {
    return await _api.get(ApiConfig.gameConfigurations);
  }

  /// Get cooldown for specific game type
  Future<ApiResponse> getGameCooldown(String gameType) async {
    return await _api.get(ApiConfig.gameCooldown(gameType));
  }

  /// Get quiz game cooldown
  Future<ApiResponse> getQuizCooldown() async {
    return await _api.get(ApiConfig.quizCooldown);
  }

  /// Get drag-drop game cooldown
  Future<ApiResponse> getDragDropCooldown() async {
    return await _api.get(ApiConfig.dragdropCooldown);
  }
}
```

### Notification Service Implementation

**File**: `lib/services/notification_service.dart`

```dart
import 'api_service.dart';
import '../config/api_config.dart';

class NotificationService {
  final ApiService _api = ApiService();

  /// Get all notifications
  Future<ApiResponse> getNotifications() async {
    return await _api.get(ApiConfig.notifications);
  }

  /// Mark notifications as viewed
  Future<ApiResponse> markNotificationsViewed() async {
    return await _api.post(ApiConfig.markNotificationsViewed, {});
  }

  /// Mark specific notification as read
  Future<ApiResponse> markNotificationRead(String notificationId) async {
    return await _api.post(
      ApiConfig.markNotificationRead(notificationId),
      {},
    );
  }

  /// Get unread notification count
  Future<ApiResponse> getUnreadCount() async {
    return await _api.get(ApiConfig.unreadCount);
  }
}
```

---

## State Management

### Using Provider (Recommended)

**File**: `lib/providers/auth_provider.dart`

```dart
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

class AuthProvider with ChangeNotifier {
  final AuthService _authService = AuthService();
  final StorageService _storage = StorageService();

  bool _isAuthenticated = false;
  bool _isLoading = true;
  String? _userId;
  Map<String, dynamic>? _userData;

  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get userId => _userId;
  Map<String, dynamic>? get userData => _userData;

  /// Initialize auth state
  Future<void> init() async {
    _isLoading = true;
    notifyListeners();

    try {
      // Check if user has valid token
      final hasToken = await _authService.isLoggedIn();
      if (hasToken) {
        final isValid = await _authService.validateToken();
        if (isValid) {
          _isAuthenticated = true;
          _userId = await _storage.getUserId();
          _userData = await _storage.getUserData();
        } else {
          await logout();
        }
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Login
  Future<LoginResult> login(String username, String password) async {
    final result = await _authService.login(username, password);
    
    if (result.success && !result.otpRequired) {
      _isAuthenticated = true;
      _userId = await _storage.getUserId();
      _userData = await _storage.getUserData();
      notifyListeners();
    }
    
    return result;
  }

  /// Logout
  Future<void> logout() async {
    await _authService.logout();
    _isAuthenticated = false;
    _userId = null;
    _userData = null;
    notifyListeners();
  }

  /// Update user data
  void updateUserData(Map<String, dynamic> data) {
    _userData = data;
    _storage.saveUserData(data);
    notifyListeners();
  }
}
```

---

## Error Handling

### Error Handler Utility

**File**: `lib/utils/error_handler.dart`

```dart
import 'package:flutter/material.dart';

class ErrorHandler {
  /// Show error dialog
  static void showErrorDialog(BuildContext context, String message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Error'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  /// Show error snackbar
  static void showErrorSnackbar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        action: SnackBarAction(
          label: 'Dismiss',
          textColor: Colors.white,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }

  /// Handle API error codes
  static String getErrorMessage(String? errorCode) {
    switch (errorCode) {
      case 'INVALID_CREDENTIALS':
        return 'Invalid username or password';
      case 'ACCOUNT_INACTIVE':
        return 'Your account has been deactivated';
      case 'ACCOUNT_NOT_APPROVED':
        return 'Your account is pending approval';
      case 'FAMILY_NOT_APPROVED':
        return 'Your family is not approved yet';
      case 'OTP_SEND_FAILED':
        return 'Failed to send OTP. Please try again';
      case 'OTP_VERIFY_FAILED':
        return 'Invalid OTP code';
      case 'NO_PHONE':
        return 'No phone number registered';
      default:
        return 'An error occurred. Please try again';
    }
  }
}
```

---

## Security Best Practices

### Security Checklist

✅ **Token Storage**
- Use `flutter_secure_storage` for tokens
- Never log tokens in console
- Clear tokens on logout

✅ **API Communication**
- Always use HTTPS in production
- Implement certificate pinning for production
- Set request timeouts

✅ **Password Handling**
- Never store passwords locally
- Implement password strength validation
- Support password visibility toggle

✅ **Biometric Authentication**
```dart
import 'package:local_auth/local_auth.dart';

class BiometricService {
  final LocalAuthentication _auth = LocalAuthentication();

  Future<bool> canUseBiometrics() async {
    return await _auth.canCheckBiometrics;
  }

  Future<bool> authenticate() async {
    try {
      return await _auth.authenticate(
        localizedReason: 'Please authenticate to login',
        options: const AuthenticationOptions(
          stickyAuth: true,
          biometricOnly: true,
        ),
      );
    } catch (e) {
      return false;
    }
  }
}
```

---

## Testing Guide

### Unit Test Example

**File**: `test/services/auth_service_test.dart`

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:your_app/services/auth_service.dart';

void main() {
  group('AuthService', () {
    test('login with valid credentials', () async {
      final authService = AuthService();
      final result = await authService.login('testuser', 'password123');
      expect(result.success, isTrue);
    });

    test('login with invalid credentials', () async {
      final authService = AuthService();
      final result = await authService.login('invalid', 'wrong');
      expect(result.success, isFalse);
    });
  });
}
```

---

## Deployment Checklist

### Pre-Deployment Steps

✅ **Update API URLs**
```dart
// api_config.dart
static const String baseUrl = 'https://your-production-url.railway.app';
```

✅ **Enable ProGuard** (Android)
```gradle
// android/app/build.gradle
buildTypes {
    release {
        minifyEnabled true
        proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
    }
}
```

✅ **Update App Icons**
- Use `flutter_launcher_icons` package
- Generate icons for all platforms

✅ **Version Management**
```yaml
# pubspec.yaml
version: 1.0.0+1
```

✅ **Build Release**
```bash
# Android
flutter build apk --release
flutter build appbundle --release

# iOS
flutter build ios --release
```

---

## Summary

### Quick Start Checklist

1. ✅ Install Flutter SDK and dependencies
2. ✅ Copy all provided code files to your project
3. ✅ Update `ApiConfig.baseUrl` with your Railway URL
4. ✅ Test login flow (username/password)
5. ✅ Test OTP flow (if enabled)
6. ✅ Test QR login
7. ✅ Test all API endpoints
8. ✅ Implement error handling
9. ✅ Add loading indicators
10. ✅ Test on physical devices
11. ✅ Build and deploy

### Key Points to Remember

🔑 **Authentication:**
- Check `otp_bypassed` flag in login response
- Use correct header format: `Token` for DRF, `Bearer` for JWT
- Handle both authentication modes gracefully

🔑 **API Calls:**
- All protected endpoints require authentication header
- Use `StorageService` for token management
- Implement proper error handling

🔑 **Security:**
- Use secure storage for tokens
- Never hardcode credentials
- Validate all user inputs

### Support & Troubleshooting

**Common Issues:**

1. **Login not working**: Check API URL and network connection
2. **Token errors**: Verify authentication header format
3. **OTP not received**: Check phone number format and SMS service

**Backend Documentation:**
- See `MOBILE_APP_OTP_BYPASS_GUIDE.md` for backend details
- Railway logs: `railway logs --service django`

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✅

For questions or support, refer to the backend team or check Railway deployment logs.
