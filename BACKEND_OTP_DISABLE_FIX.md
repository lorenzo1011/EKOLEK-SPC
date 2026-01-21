# Django Backend: Fix OTP Disabled Mode

**Problem**: Backend is returning `otp_sent: true` instead of `otp_bypassed: true` when OTP should be disabled.

**Root Cause**: Environment variable `OTP_VERIFICATION_ENABLED` is either:
- Not set on Railway
- Set incorrectly (wrong value)
- Django settings.py not reading it properly
- Backend not redeployed after setting variable

---

## Step 1: Check Django Settings Configuration

### Open your Django `settings.py` file

Look for this line (should be near the top with other imports):

```python
import os
```

Then add this line in the settings section (after `DEBUG` setting is good):

```python
# OTP Verification Feature Flag
OTP_VERIFICATION_ENABLED = os.getenv('OTP_VERIFICATION_ENABLED', 'True') == 'True'
```

**Explanation:**
- `os.getenv('OTP_VERIFICATION_ENABLED', 'True')` reads from environment variable
- Default is `'True'` (string) if not set
- `== 'True'` converts string to boolean
- Result: `True` or `False` boolean value

### ✅ Verify This Code Exists in Your Settings

Check these lines are in your `settings.py`:

```python
import os
from pathlib import Path

# ... other settings ...

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# OTP Verification Feature Flag
OTP_VERIFICATION_ENABLED = os.getenv('OTP_VERIFICATION_ENABLED', 'True') == 'True'

# ... rest of settings ...
```

---

## Step 2: Set Environment Variable on Railway

### Go to Railway Dashboard

1. **Login**: https://railway.app
2. **Select your Django project**
3. **Click on your Django service** (not the database)
4. **Click "Variables" tab**

### Add the Environment Variable

Click **"+ New Variable"** button and add:

```
Variable Name: OTP_VERIFICATION_ENABLED
Variable Value: False
```

**⚠️ IMPORTANT:**
- Use exactly `False` with capital F
- NOT `false` or `FALSE` or `0`
- Case sensitive!

### Screenshot of Correct Setup

```
┌─────────────────────────────────────────┐
│ Environment Variables                    │
├─────────────────────────────────────────┤
│ OTP_VERIFICATION_ENABLED    False      │
│ DEBUG                        False      │
│ SECRET_KEY                   ******     │
│ DATABASE_URL                 ******     │
└─────────────────────────────────────────┘
```

---

## Step 3: Redeploy on Railway

### Trigger Redeployment

**Option A: Redeploy Button**
1. Stay in your Django service
2. Click **"Deployments"** tab
3. Click **"Redeploy"** button on the latest deployment

**Option B: Git Push**
1. Make a small change to any file
2. Commit and push to your repository
3. Railway will auto-deploy

### Wait for Deployment

- Watch the **"Deployments"** tab
- Wait until status shows **"Success" ✅**
- Usually takes 2-3 minutes

---

## Step 4: Verify Backend Response

### Test with curl (Command Line)

```bash
curl -X POST https://your-app.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"test_password"}'
```

### Expected Response (OTP Disabled - CORRECT):

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
    "gender": "male",
    "phone": "+639123456789",
    "status": "approved",
    "is_family_representative": true
  },
  "family_info": {
    "id": "family-uuid",
    "family_name": "Test Family",
    "family_code": "TSTFAM123",
    "barangay": "Barangay Test",
    "status": "approved"
  }
}
```

### Wrong Response (OTP Still Enabled - INCORRECT):

```json
{
  "success": true,
  "otp_sent": true,
  "user_id": "12345-67890-abcdef"
}
```

---

## Step 5: Check Railway Logs

If still not working, check the logs:

### View Logs on Railway

1. Go to your Django service
2. Click **"Logs"** tab
3. Look for these messages:

**Should see (OTP Disabled):**
```
[OTP BYPASS] OTP verification is disabled. Issuing token directly for user: test_user
Login successful (OTP disabled) for user: test_user
```

**Should NOT see (OTP Enabled):**
```
Sending OTP to phone: +639XXXXXXXX
OTP sent successfully to user: test_user
```

### Check Environment Variable in Logs

Look for Django startup logs:
```
OTP_VERIFICATION_ENABLED = False
```

If you see `True`, the environment variable isn't being read correctly.

---

## Step 6: Troubleshooting

### Problem: Still returning `otp_sent: true`

**Solution 1: Check Variable Name**
- Must be exactly: `OTP_VERIFICATION_ENABLED`
- No extra spaces
- No typos

**Solution 2: Check Variable Value**
- Must be exactly: `False` (capital F)
- NOT `false`, `FALSE`, `0`, or `no`

**Solution 3: Force Redeploy**
1. Delete the environment variable
2. Save changes
3. Re-add the variable with `False`
4. Redeploy again

**Solution 4: Check settings.py**
Make sure this line exists:
```python
OTP_VERIFICATION_ENABLED = os.getenv('OTP_VERIFICATION_ENABLED', 'True') == 'True'
```

### Problem: Backend returns error 500

**Check Django Logs** for error messages:
```
railway logs --follow
```

Common issues:
- Database connection error
- Missing user data
- Family not found

### Problem: Token format wrong

**Check response** has these fields:
- `token` (string)
- `user_info` (object)
- `family_info` (object)

If missing, check `django_otp_views.py` lines 66-98.

---

## Complete Django Settings Example

Your `settings.py` should have this section:

```python
# settings.py

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# OTP Verification Feature Flag
# Set to False to disable OTP and allow direct login
OTP_VERIFICATION_ENABLED = os.getenv('OTP_VERIFICATION_ENABLED', 'True') == 'True'

ALLOWED_HOSTS = ['*']  # Configure properly for production

# ... rest of your settings ...
```

---

## Railway Environment Variables Checklist

Verify you have these set:

- [ ] `SECRET_KEY` - Django secret key
- [ ] `DEBUG` - Set to `False` for production
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `OTP_VERIFICATION_ENABLED` - Set to `False` ✅
- [ ] `TWILIO_ACCOUNT_SID` - (Can be empty if OTP disabled)
- [ ] `TWILIO_AUTH_TOKEN` - (Can be empty if OTP disabled)
- [ ] `TWILIO_PHONE_NUMBER` - (Can be empty if OTP disabled)

---

## Backend Code Verification

### Check `django_otp_views.py`

Lines 18-20 should have:

```python
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# OTP Verification Feature Flag
OTP_VERIFICATION_ENABLED = getattr(settings, 'OTP_VERIFICATION_ENABLED', True)
```

### Check `login_view` function

Lines 65-98 should contain the bypass logic:

```python
# If OTP verification is disabled, skip OTP and issue token directly
if not OTP_VERIFICATION_ENABLED:
    logger.info(f"[OTP BYPASS] OTP verification is disabled. Issuing token directly for user: {user.username}")
    
    # Create or get DRF Token
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=user)
    
    # Build complete response with user and family data
    return Response({
        'success': True,
        'message': 'Login successful (OTP disabled)',
        'otp_bypassed': True,
        'token': token.key,
        'user_info': {
            'id': str(user.id),
            'username': user.username,
            'full_name': getattr(user, 'full_name', ''),
            'total_points': getattr(user, 'total_points', 0),
            'gender': getattr(user, 'gender', ''),
            'phone': getattr(user, 'phone', ''),
            'status': getattr(user, 'status', 'approved'),
            'is_family_representative': getattr(user, 'is_family_representative', False),
        },
        'family_info': {
            'id': str(user.family.id) if user.family else None,
            'family_name': user.family.family_name if user.family else '',
            'family_code': user.family.family_code if user.family else '',
            'barangay': user.family.barangay.name if user.family and user.family.barangay else '',
            'status': user.family.status if user.family else 'approved',
        }
    }, status=200)
```

If this code is missing or different, the backend won't work correctly.

---

## Testing After Fix

### 1. Test Login Endpoint

```bash
curl -X POST https://your-app.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

### 2. Test QR Login Endpoint

```bash
curl -X POST https://your-app.railway.app/api/qr-login/ \
  -H "Content-Type: application/json" \
  -d '{
    "qr_code": "your_qr_code"
  }'
```

### 3. Expected Success Response

Both endpoints should return:
```json
{
  "success": true,
  "otp_bypassed": true,
  "token": "abc123...",
  "user_info": { ... },
  "family_info": { ... }
}
```

### 4. Test Token Works

```bash
curl -X GET https://your-app.railway.app/api/current_user_data/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

Should return 200 with user data.

---

## Summary Checklist

Before testing your Flutter app:

- [ ] Django `settings.py` has `OTP_VERIFICATION_ENABLED` line
- [ ] Railway environment variable set to `False`
- [ ] Railway deployment successful
- [ ] Backend logs show `[OTP BYPASS]` message
- [ ] `/api/login/` returns `otp_bypassed: true`
- [ ] Response includes `token`, `user_info`, `family_info`
- [ ] Token authentication works with `Authorization: Token abc123`

---

## Need Help?

### Check These First:

1. **Railway Logs**: Look for error messages
   ```
   Settings: OTP_VERIFICATION_ENABLED = False
   [OTP BYPASS] OTP verification is disabled
   ```

2. **Test Endpoint Directly**: Use curl or Postman
   - Verify exact response format
   - Check for `otp_bypassed: true`

3. **Environment Variables**: Double-check spelling and value

### Common Mistakes:

❌ Variable value: `false` (lowercase)  
✅ Variable value: `False` (capital F)

❌ Variable name: `OTP_ENABLED`  
✅ Variable name: `OTP_VERIFICATION_ENABLED`

❌ Forgot to redeploy after setting variable  
✅ Always redeploy after changing variables

---

**Once this is fixed, your Flutter app will work without any changes!**

The frontend is already correctly implemented to check for `otp_bypassed` flag.
