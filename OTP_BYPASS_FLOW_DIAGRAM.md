# OTP Bypass Feature - Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OTP VERIFICATION CONTROL                         │
│                     (OTP_VERIFICATION_ENABLED Flag)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                  │
                     ▼                                  ▼
          ┌──────────────────┐              ┌──────────────────┐
          │   TRUE (default) │              │   FALSE (bypass) │
          │  OTP ENABLED     │              │  OTP DISABLED    │
          └──────────────────┘              └──────────────────┘
                     │                                  │
                     │                                  │
┌────────────────────┴─────────────────┐   ┌───────────┴──────────────────┐
│        NORMAL OPERATION              │   │      BYPASS MODE             │
│                                      │   │                              │
│  USER REGISTRATION:                  │   │  USER REGISTRATION:          │
│  ├─ Phone OTP required ✓            │   │  ├─ Phone OTP skipped ✗     │
│  ├─ Email OTP required ✓            │   │  ├─ Email OTP skipped ✗     │
│  └─ Must verify both to register    │   │  └─ Register immediately     │
│                                      │   │                              │
│  WEB LOGIN:                          │   │  WEB LOGIN:                  │
│  ├─ Username/password                │   │  ├─ Username/password        │
│  ├─ Send OTP to phone ✓             │   │  └─ Login directly ✗        │
│  ├─ Verify OTP code                  │   │                              │
│  └─ Login on success                 │   │                              │
│                                      │   │                              │
│  MOBILE LOGIN:                       │   │  MOBILE LOGIN:               │
│  ├─ Username/password                │   │  ├─ Username/password        │
│  ├─ Send OTP to phone ✓             │   │  ├─ Issue token directly ✗  │
│  ├─ Verify OTP code                  │   │  └─ Skip OTP screen          │
│  └─ Issue token on success           │   │                              │
│                                      │   │                              │
│  QR LOGIN:                           │   │  QR LOGIN:                   │
│  ├─ Scan QR code                     │   │  ├─ Scan QR code             │
│  ├─ Send OTP to phone ✓             │   │  ├─ Login/token directly ✗  │
│  ├─ Verify OTP code                  │   │  └─ Skip OTP screen          │
│  └─ Login/token on success           │   │                              │
│                                      │   │                              │
└──────────────────────────────────────┘   └──────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                           SMS OTP SERVICE FLOW
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                         send_otp(phone_number)                           │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │ Check OTP_VERIFICATION_ENABLED │
                   └──────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                  │
                 ▼                                  ▼
      ┌─────────────────┐              ┌─────────────────────┐
      │   TRUE (normal) │              │   FALSE (bypass)    │
      └─────────────────┘              └─────────────────────┘
                 │                                  │
                 ▼                                  ▼
    ┌────────────────────────┐        ┌─────────────────────────┐
    │ Check rate limit       │        │ Return success          │
    │ Generate OTP code      │        │ No SMS sent             │
    │ Store in Redis         │        │ No API call             │
    │ Call SMS API           │        │ No charge incurred      │
    │ Send SMS               │        │ bypass_mode: true       │
    │ Return response        │        │ otp_code: '000000'      │
    └────────────────────────┘        └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    verify_otp(phone_number, otp_code)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │ Check OTP_VERIFICATION_ENABLED │
                   └──────────────────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │                                  │
                 ▼                                  ▼
      ┌─────────────────┐              ┌─────────────────────┐
      │   TRUE (normal) │              │   FALSE (bypass)    │
      └─────────────────┘              └─────────────────────┘
                 │                                  │
                 ▼                                  ▼
    ┌────────────────────────┐        ┌─────────────────────────┐
    │ Check rate limit       │        │ Return success          │
    │ Get OTP from Redis     │        │ Auto-approve            │
    │ Check expiration       │        │ No validation           │
    │ Compare codes          │        │ bypass_mode: true       │
    │ Clear on success       │        │ status: 'success'       │
    │ Increment on fail      │        │                         │
    │ Return result          │        │                         │
    └────────────────────────┘        └─────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                          EMAIL OTP SERVICE FLOW
═══════════════════════════════════════════════════════════════════════════

Same logic as SMS OTP, but for email:
- send_otp(email) - bypasses SendGrid API when disabled
- verify_otp(email, otp_code) - auto-approves when disabled


═══════════════════════════════════════════════════════════════════════════
                        MOBILE LOGIN API FLOW
═══════════════════════════════════════════════════════════════════════════

POST /api/login/
┌─────────────────────────────────────┐
│ Validate username/password          │
│ Check account status                │
└─────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────┐
│ Check OTP_VERIFICATION_ENABLED       │
└──────────────────────────────────────┘
                │
   ┌────────────┴────────────┐
   │                         │
   ▼                         ▼
[ENABLED]                [DISABLED]
   │                         │
   ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ Send OTP         │    │ Create token         │
│ Store session    │    │ Return user info     │
│ Return:          │    │ Return:              │
│ {                │    │ {                    │
│   success: true, │    │   success: true,     │
│   otp_sent: true,│    │   otp_bypassed: true,│
│   user_id: ...   │    │   token: ...,        │
│ }                │    │   user_info: {...}   │
└──────────────────┘    │ }                    │
                        └──────────────────────┘


POST /api/login/verify-otp/
┌─────────────────────────────────────┐
│ Validate user_id and otp            │
│ Call verify_otp(phone, otp)         │
│ Create token on success             │
│ Return user info and token          │
└─────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                         DEPLOYMENT DIAGRAM
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                        LOCAL DEVELOPMENT                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Update .env file:                                                   │
│     OTP_VERIFICATION_ENABLED=False                                      │
│                                                                          │
│  2. Restart server:                                                     │
│     python manage.py runserver                                          │
│                                                                          │
│  3. Test authentication flows                                           │
│                                                                          │
│  4. Check logs for:                                                     │
│     [OTP BYPASS] messages                                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      RAILWAY PRODUCTION                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Railway Dashboard → Project → Variables                             │
│                                                                          │
│  2. Add/Update:                                                         │
│     ┌───────────────────────────────────────────────────┐              │
│     │ Name:  OTP_VERIFICATION_ENABLED                   │              │
│     │ Value: False  (to disable)                        │              │
│     │        True   (to enable)                         │              │
│     └───────────────────────────────────────────────────┘              │
│                                                                          │
│  3. Deploy/Restart service                                              │
│                                                                          │
│  4. Monitor Railway logs for:                                           │
│     [OTP BYPASS] messages                                               │
│                                                                          │
│  5. Test authentication flows                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
                         SECURITY LAYERS
═══════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION SECURITY LAYERS                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Layer 1: Username/Password ✓ ALWAYS ACTIVE                            │
│  ├─ Password hashing                                                    │
│  ├─ Password complexity rules                                           │
│  └─ Secure password storage                                             │
│                                                                          │
│  Layer 2: OTP Verification ⚡ CONFIGURABLE                              │
│  ├─ SMS OTP (when enabled)                                              │
│  ├─ Email OTP (when enabled)                                            │
│  └─ Can be temporarily disabled                                         │
│                                                                          │
│  Layer 3: Account Approval ✓ ALWAYS ACTIVE                             │
│  ├─ Admin must approve new users                                        │
│  ├─ Status check on login                                               │
│  └─ Family approval check                                               │
│                                                                          │
│  Layer 4: Rate Limiting ✓ ALWAYS ACTIVE                                │
│  ├─ Failed login attempts tracking                                      │
│  ├─ IP-based rate limiting                                              │
│  └─ Account lockout after threshold                                     │
│                                                                          │
│  Layer 5: Session Management ✓ ALWAYS ACTIVE                           │
│  ├─ Secure session cookies                                              │
│  ├─ CSRF protection                                                     │
│  └─ Token-based auth (mobile)                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

⚠️  NOTE: Disabling OTP removes Layer 2 only.
    All other security layers remain fully active.


═══════════════════════════════════════════════════════════════════════════
                       QUICK REFERENCE COMMANDS
═══════════════════════════════════════════════════════════════════════════

# Check current OTP status in logs:
grep "OTP BYPASS" railway.log

# Enable OTP (in .env):
OTP_VERIFICATION_ENABLED=True

# Disable OTP (in .env):
OTP_VERIFICATION_ENABLED=False

# Default (if not set):
# Defaults to True (OTP enabled)

# Restart Django:
python manage.py runserver

# Check Django settings:
python manage.py shell
>>> from django.conf import settings
>>> settings.OTP_VERIFICATION_ENABLED
True

═══════════════════════════════════════════════════════════════════════════
```

**Last Updated**: January 21, 2026  
**Status**: Production Ready ✅
