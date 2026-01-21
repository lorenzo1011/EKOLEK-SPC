# 🚀 RAILWAY SETUP - FINAL STEPS

## ⚡ URGENT: Complete These Steps NOW

### Step 1: Set Railway Environment Variable (2 minutes)

1. **Go to Railway Dashboard**
   - URL: https://railway.app/dashboard
   - Login with your account

2. **Select Your Project**
   - Find: `kolek` or `e-kolek` project
   - Click on the project

3. **Open Variables Tab**
   - Click on your service/deployment
   - Click "Variables" tab on the left

4. **Add This Variable**
   ```
   Variable Name: OTP_VERIFICATION_ENABLED
   Value: False
   ```
   
   **COPY THIS EXACTLY:**
   ```
   OTP_VERIFICATION_ENABLED
   ```
   
   **Value must be one of these:**
   - `False` (recommended)
   - `false`
   - `0`
   - `no`

5. **Click "Add Variable"**
   - Railway will automatically redeploy
   - Takes 2-3 minutes

---

## Step 2: Verify Deployment (3 minutes)

### Check Railway Logs

1. **Open Deployments Tab**
   - Railway Dashboard → Your Project → Deployments

2. **Click Latest Deployment**
   - Should show "Building..." then "Active"
   - Wait for "Active" status

3. **View Logs**
   - Click "View Logs" button
   - Search for this text:
   
   **LOOK FOR THIS:**
   ```
   🔐 OTP Configuration: OTP_VERIFICATION_ENABLED = False
   ⚠️  OTP VERIFICATION IS DISABLED - Mobile login will skip OTP step
   ```

4. **Verify Status**
   - ✅ See `OTP_VERIFICATION_ENABLED = False` → **SUCCESS!**
   - ❌ See `OTP_VERIFICATION_ENABLED = True` → Variable not set correctly, try again

---

## Step 3: Test Backend (5 minutes)

### Option A: Use Test Script (Local)

```bash
# If testing locally
python test_otp_config.py
```

**Expected Output:**
```
✅ OTP_VERIFICATION_ENABLED = False
✅ OTP IS DISABLED - Mobile login will bypass OTP
```

### Option B: Test Railway API (Recommended)

**Get Your Railway URL:**
- Railway Dashboard → Your Service → Settings → Domain
- Should be like: `https://your-app.up.railway.app`

**Test with Curl (PowerShell):**
```powershell
# Replace with your Railway URL and credentials
$url = "https://your-app.up.railway.app/api/login/"
$body = @{
    username = "your_username"
    password = "your_password"
} | ConvertTo-Json

Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/json"
```

**Expected Response:**
```json
{
  "otp_bypassed": true,
  "token": "abc123...",
  "user_info": {
    "user_id": 1,
    "username": "your_username",
    "email": "email@example.com"
  }
}
```

**Wrong Response (If OTP still enabled):**
```json
{
  "otp_sent": true,
  "user_id": 1
}
```

---

## Step 4: Test Flutter App (5 minutes)

### Mobile App Testing

1. **Open Flutter App**
   - Make sure app uses Railway backend URL

2. **Try Login**
   - Enter username and password
   - Click "Login" button

3. **Expected Behavior:**
   - ✅ No OTP screen shows up
   - ✅ Goes directly to home screen
   - ✅ No "Token refresh failed" error
   - ✅ Data loads (schedules, games, notifications)

4. **Wrong Behavior (If not working):**
   - ❌ OTP screen shows up
   - ❌ "Token refresh failed" error
   - ❌ Stuck on login screen

---

## 🔧 TROUBLESHOOTING

### Problem: OTP Still Enabled

**Check 1: Variable Name**
- Must be exactly: `OTP_VERIFICATION_ENABLED`
- Case-sensitive!
- No extra spaces

**Check 2: Variable Value**
- Must be: `False`, `false`, `0`, or `no`
- NOT: `"False"` (with quotes)
- NOT: `TRUE` or `True`

**Check 3: Redeploy**
```bash
# Force redeploy if needed
git commit --allow-empty -m "Force redeploy"
git push origin master
```

**Check 4: Clear Railway Cache**
1. Delete the variable
2. Wait 30 seconds
3. Add it again with correct value
4. Wait for full redeploy (3-5 minutes)

---

### Problem: Backend Returns Error

**Check Django Logs:**
1. Railway → Deployments → Latest → View Logs
2. Look for error messages
3. Common issues:
   - User doesn't exist
   - Wrong password
   - Database connection issue

**Create Test User:**
```bash
# SSH into Railway (if available)
python manage.py createsuperuser --username testuser --email test@test.com
```

---

## ✅ COMPLETION CHECKLIST

Mark each when done:

- [ ] **Set Railway Variable**
  - Variable: `OTP_VERIFICATION_ENABLED = False`

- [ ] **Verify Deployment**
  - Logs show: `OTP_VERIFICATION_ENABLED = False`

- [ ] **Test Backend API**
  - Response has: `otp_bypassed: true`
  - Response has: `token: "..."`

- [ ] **Test Flutter App**
  - Login works without OTP screen
  - No "Token refresh failed" error
  - Data loads correctly

- [ ] **Ready for Presentation** 🎉
  - All features working
  - No errors
  - Demo-ready!

---

## 📞 QUICK HELP

### Common Values for Railway Variable

| Value | Works? | Notes |
|-------|--------|-------|
| `False` | ✅ Yes | Recommended |
| `false` | ✅ Yes | Also works |
| `0` | ✅ Yes | Also works |
| `no` | ✅ Yes | Also works |
| `"False"` | ❌ No | Don't use quotes |
| `TRUE` | ❌ No | Wrong value |
| (empty) | ❌ No | Must have value |

### Railway Dashboard URLs

- **Main Dashboard:** https://railway.app/dashboard
- **Project Settings:** Click project → Settings
- **Environment Variables:** Click project → Variables
- **Deployment Logs:** Click project → Deployments → View Logs

---

## 🎯 EXPECTED TIMELINE

| Step | Time | Status |
|------|------|--------|
| Set variable | 2 min | ⏳ Do now |
| Railway deploys | 3 min | ⏳ Wait |
| Test backend | 2 min | ⏳ After deploy |
| Test mobile app | 3 min | ⏳ Final check |
| **Total** | **10 min** | **Ready!** |

---

## 🚀 YOU'RE ALMOST DONE!

1. Set the Railway variable: `OTP_VERIFICATION_ENABLED = False`
2. Wait 3 minutes for deployment
3. Test mobile app login
4. **Ready for presentation tomorrow!** 🎉

Good luck with your presentation! 💪
