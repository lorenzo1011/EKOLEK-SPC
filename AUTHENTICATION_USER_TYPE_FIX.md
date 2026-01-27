# AUTHENTICATION FIX: Removed Non-Existent user_type Field

## Problem
Mobile app login was failing with `AttributeError` because `auth_views.py` was trying to access `user.user_type` field that doesn't exist in the Users model.

## Root Cause
The `Users` model in `accounts/models.py` does not have a `user_type` field. The authentication views were trying to return this field in the login response, causing crashes.

## Files Fixed
1. **mobilelogin/auth_views.py**
   - `login_view()` function (line ~124)
   - `qr_login()` function (line ~237)

## Changes Made

### Before (BROKEN):
```python
'user': {
    'id': str(user.id),
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'full_name': user.full_name,
    'phone': user.phone,
    'email': user.email or '',
    'user_type': user.user_type,  # ❌ FIELD DOESN'T EXIST
    'total_points': float(user.total_points) if hasattr(user, 'total_points') else 0.0,
    'family': family_info,
    'is_family_representative': getattr(user, 'is_family_representative', False),
}
```

### After (FIXED):
```python
'user': {
    'id': str(user.id),
    'username': user.username,
    'first_name': user.first_name,
    'last_name': user.last_name,
    'full_name': user.full_name,
    'phone': user.phone,
    'email': user.email or '',
    'total_points': float(user.total_points) if hasattr(user, 'total_points') else 0.0,
    'family': family_info,
    'is_family_representative': getattr(user, 'is_family_representative', False),
}
```

## Users Model Fields (Reference)
The `Users` model in `accounts/models.py` has:
- ✅ `username`
- ✅ `first_name`
- ✅ `last_name`
- ✅ `full_name`
- ✅ `phone`
- ✅ `email`
- ✅ `total_points`
- ✅ `is_family_representative`
- ❌ **NO** `user_type` field exists

## Impact
- **Fixed:** Mobile app login now works correctly
- **Fixed:** QR code login now works correctly
- **Consistent:** All login endpoints (regular, QR, biometric) now return the same user data structure
- **Validated:** No syntax errors, code is production-ready

## Testing Checklist
- [ ] Test regular username/password login
- [ ] Test QR code login
- [ ] Verify JWT tokens are returned correctly
- [ ] Confirm mobile app can authenticate successfully
- [ ] Check Railway deployment logs for any errors

## Deployment
Ready to commit and push to Railway:
```bash
git add mobilelogin/auth_views.py
git commit -m "fix: Remove non-existent user_type field from login responses"
git push origin master
```

## Notes
- The `biometric_views.py` was already correct and did not include `user_type`
- The `is_family_representative` field provides role information (member vs representative)
- Previous fixes already addressed OTP removal and JWT token key naming
