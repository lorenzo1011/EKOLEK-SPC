# OTP Bypass Feature Guide

## Overview

The E-KOLEK system now supports **temporary disabling of OTP verification** for both SMS and Email authentication. This feature is controlled by a single configuration flag and can be easily toggled on/off without code changes.

## Configuration

### Environment Variable

Add the following to your `.env` file:

```bash
# OTP Verification Control
# Set to False to disable OTP verification (default: True)
OTP_VERIFICATION_ENABLED=False
```

### Values

- `True` (default) - OTP verification is **ENABLED** (normal operation)
- `False` - OTP verification is **DISABLED** (bypass mode)

## What Gets Bypassed

When `OTP_VERIFICATION_ENABLED=False`, the following authentication flows will bypass OTP:

### 1. User Registration
- ✅ Family registration (web)
- ✅ Member registration (web)
- ✅ Both SMS and Email OTP checks are bypassed
- ✅ Users can complete registration without OTP verification

### 2. User Login (Web)
- ✅ Standard login (username/password)
- ✅ Code login (direct login)
- ✅ QR code login
- ✅ Users are logged in immediately without OTP step

### 3. Mobile App Login
- ✅ Mobile login (username/password + OTP)
- ✅ Mobile QR login
- ✅ Token is issued immediately without OTP verification

## How It Works

### SMS OTP Service (`accounts/otp_service.py`)

**send_otp():**
- When disabled: Returns success immediately without sending SMS
- No API calls are made
- No charges incurred from SMS provider

**verify_otp():**
- When disabled: Always returns success regardless of OTP code
- No verification logic executed

### Email OTP Service (`accounts/email_otp_service.py`)

**send_otp():**
- When disabled: Returns success immediately without sending email
- No Celery tasks queued
- No SendGrid API calls made

**verify_otp():**
- When disabled: Always returns success regardless of OTP code
- No verification logic executed

### Response Format

When bypass mode is active, services return:

```python
{
    'success': True,
    'message': 'OTP verification disabled - bypass mode active',
    'bypass_mode': True,
    'data': {
        'otp_code': '000000',  # Placeholder
        'phone_number': '...'  # or 'email': '...'
    }
}
```

## Security Considerations

⚠️ **IMPORTANT SECURITY NOTES:**

1. **Temporary Use Only**: This feature is designed for temporary disabling of OTP. It should NOT be permanently disabled in production.

2. **Production Usage**: Only disable OTP when:
   - Migrating authentication systems
   - Testing new authentication flows
   - Emergency situations (SMS provider down, etc.)
   - Temporarily removing friction during user migration

3. **Re-enable ASAP**: Always re-enable OTP verification as soon as possible to maintain security standards.

4. **Rate Limiting**: Even with OTP disabled, standard rate limiting on login attempts still applies.

5. **Other Security Measures**: All other security measures remain active:
   - Password authentication
   - Account approval workflow
   - Session management
   - CSRF protection
   - Rate limiting on failed attempts

## Testing

### Local Development

1. Set in `.env`:
   ```bash
   OTP_VERIFICATION_ENABLED=False
   ```

2. Restart Django server:
   ```bash
   python manage.py runserver
   ```

3. Test registration/login flows - should skip OTP steps

### Railway Production

1. Set environment variable in Railway dashboard:
   - Go to your project
   - Navigate to Variables
   - Add: `OTP_VERIFICATION_ENABLED` = `False`

2. Redeploy or restart service

3. Verify logs show bypass messages:
   ```
   [OTP BYPASS] OTP verification is disabled - skipping SMS send
   [OTP BYPASS] OTP verification is disabled - auto-approving verification
   ```

## Re-enabling OTP

To re-enable OTP verification:

### Local Development
1. Update `.env`:
   ```bash
   OTP_VERIFICATION_ENABLED=True
   ```
   Or simply remove/comment out the line (defaults to True)

2. Restart server

### Railway Production
1. Update environment variable to `True` or delete it
2. Redeploy/restart service

## Logs and Monitoring

When bypass mode is active, you'll see these log messages:

**SMS OTP:**
```
[OTP BYPASS] OTP verification is disabled - skipping SMS send
[INFO] OTP Verification DISABLED - Bypassing SMS send
```

**Email OTP:**
```
[OTP BYPASS] OTP verification is disabled - skipping email send
```

**Login/Registration:**
```
[OTP BYPASS] Skipping OTP for user {username} - logging in directly
[OTP BYPASS] Skipping OTP checks for family registration
```

## Mobile App Compatibility

The mobile app will automatically handle bypass mode:

### Login Response (OTP Disabled)
```json
{
  "success": true,
  "message": "Login successful (OTP disabled)",
  "otp_bypassed": true,
  "token": "abc123...",
  "user_info": {
    "id": "...",
    "username": "...",
    "full_name": "...",
    "total_points": 0,
    "status": "approved"
  },
  "family_info": {...}
}
```

### Expected Mobile App Behavior
1. Check for `otp_bypassed: true` in response
2. If present, skip OTP verification screen
3. Proceed directly to home screen with token

## Implementation Details

### Files Modified

1. **Settings** (`eko/settings.py`)
   - Added `OTP_VERIFICATION_ENABLED` configuration flag

2. **SMS OTP Service** (`accounts/otp_service.py`)
   - Bypass check in `send_otp()`
   - Bypass check in `verify_otp()`

3. **Email OTP Service** (`accounts/email_otp_service.py`)
   - Bypass check in `send_otp()`
   - Bypass check in `verify_otp()`

4. **Mobile Login Views** (`mobilelogin/django_otp_views.py`)
   - Direct token issuance when OTP disabled
   - Updated `login_view()` and `qr_login()`

5. **Web Login Views** (`accounts/views/auth_views.py`)
   - Direct login when OTP disabled
   - Updated `login_page()`, `code_login()`, and QR login

6. **Registration Views** (`accounts/views/registration_views.py`)
   - Skip OTP checks when disabled
   - Updated `register_family()` and `register_member()`

7. **OTP Views** (`accounts/views/otp_views.py`)
   - Added flag for consistency

## Troubleshooting

### Issue: OTP still being sent
**Solution:** 
- Verify `.env` has `OTP_VERIFICATION_ENABLED=False`
- Restart Django server
- Check logs for "[OTP BYPASS]" messages

### Issue: Mobile app still shows OTP screen
**Solution:**
- Update mobile app to check `otp_bypassed` flag in response
- If flag is true, skip OTP screen and proceed with token

### Issue: Registration still requires OTP
**Solution:**
- Clear browser cache
- Ensure server restarted after setting flag
- Check server logs for bypass messages

## Best Practices

1. **Document Changes**: Always document when and why OTP was disabled
2. **Set Reminders**: Set a reminder to re-enable OTP after temporary use
3. **Monitor Logs**: Watch for unusual login patterns when OTP is disabled
4. **Communicate**: Inform team/stakeholders when OTP is temporarily disabled
5. **Test First**: Always test in development before applying to production

## Example: Disabling OTP for User Migration

**Scenario**: Migrating 500+ existing users from old system

**Steps:**
1. Announce maintenance window
2. Set `OTP_VERIFICATION_ENABLED=False` in production
3. Import users and have them login/register without OTP friction
4. Monitor for 24-48 hours
5. Re-enable: `OTP_VERIFICATION_ENABLED=True`
6. Announce OTP re-enabled

## Support

For issues or questions:
- Check server logs for bypass messages
- Verify environment variable is set correctly
- Ensure server was restarted after config change
- Contact development team if issues persist

---

**Last Updated**: January 21, 2026
**Version**: 1.0
**Status**: Production Ready ✅
