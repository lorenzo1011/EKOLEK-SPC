# Quick Reference: Disable/Enable OTP

## To DISABLE OTP Verification

### Option 1: Environment Variable (.env file)
Add to your `.env` file:
```bash
OTP_VERIFICATION_ENABLED=False
```

### Option 2: Railway Dashboard
1. Open your Railway project
2. Go to Variables section
3. Add new variable:
   - Name: `OTP_VERIFICATION_ENABLED`
   - Value: `False`
4. Redeploy/restart service

### Restart Required
After setting the variable, restart your Django server:
```bash
# Local
python manage.py runserver

# Railway
# Automatic on redeploy or manual restart
```

---

## To RE-ENABLE OTP Verification

### Option 1: Environment Variable (.env file)
Update your `.env` file:
```bash
OTP_VERIFICATION_ENABLED=True
```
Or simply remove/comment out the line (defaults to True):
```bash
# OTP_VERIFICATION_ENABLED=False
```

### Option 2: Railway Dashboard
1. Open your Railway project
2. Go to Variables section
3. Either:
   - Change `OTP_VERIFICATION_ENABLED` to `True`
   - Or delete the variable (defaults to True)
4. Redeploy/restart service

### Restart Required
Restart your Django server after the change.

---

## Verify Status

### Check Logs
When OTP is **DISABLED**, you'll see:
```
[OTP BYPASS] OTP verification is disabled - skipping SMS send
[OTP BYPASS] OTP verification is disabled - auto-approving verification
```

When OTP is **ENABLED** (normal), you'll see:
```
=== iProg Tech SMS API for OTP ===
[REQUEST] Endpoint: https://www.iprogsms.com/api/v1/sms_messages
[RESULT] API Response: {...}
```

### Test Login
- **OTP Disabled**: Login completes immediately without OTP step
- **OTP Enabled**: System prompts for OTP code

---

## What This Controls

✅ User Registration (web)  
✅ User Login (web)  
✅ Mobile App Login  
✅ QR Code Login  
✅ Both SMS and Email OTP  

---

## Important Notes

⚠️ **Use temporarily only** - Re-enable OTP as soon as possible  
⚠️ **Security**: Other security measures (passwords, rate limiting) remain active  
⚠️ **Production**: Test in development first before applying to production  

---

## Common Use Cases

- **User Migration**: Temporarily disable during bulk user import
- **Testing**: Disable for easier testing of registration/login flows
- **SMS Provider Issues**: Bypass OTP when SMS service is down
- **Emergency Access**: Temporary bypass for critical situations

---

**Quick Toggle Command**

Create a script `toggle_otp.sh` (Linux/Mac) or `toggle_otp.bat` (Windows):

```bash
# toggle_otp.sh
#!/bin/bash
if grep -q "OTP_VERIFICATION_ENABLED=False" .env; then
    sed -i 's/OTP_VERIFICATION_ENABLED=False/OTP_VERIFICATION_ENABLED=True/' .env
    echo "✅ OTP ENABLED"
else
    sed -i 's/OTP_VERIFICATION_ENABLED=True/OTP_VERIFICATION_ENABLED=False/' .env
    echo "❌ OTP DISABLED"
fi
echo "Restart Django server for changes to take effect"
```

```batch
REM toggle_otp.bat (Windows)
@echo off
findstr /C:"OTP_VERIFICATION_ENABLED=False" .env >nul
if %errorlevel%==0 (
    powershell -Command "(gc .env) -replace 'OTP_VERIFICATION_ENABLED=False', 'OTP_VERIFICATION_ENABLED=True' | Out-File -encoding ASCII .env"
    echo OTP ENABLED
) else (
    powershell -Command "(gc .env) -replace 'OTP_VERIFICATION_ENABLED=True', 'OTP_VERIFICATION_ENABLED=False' | Out-File -encoding ASCII .env"
    echo OTP DISABLED
)
echo Restart Django server for changes to take effect
```

Make executable:
```bash
chmod +x toggle_otp.sh
```

Usage:
```bash
./toggle_otp.sh
# or
toggle_otp.bat
```

---

**Last Updated**: January 21, 2026
