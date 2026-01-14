# iProg SMS API Update - January 14, 2026

## Important Changes Implemented

This document describes the iProg SMS API update implemented on January 14, 2026, affecting how SMS messages are sent in the E-KOLEK system.

---

## 📊 Daily Limit System

**What Changed:**
- iProg SMS now implements a daily limit system for fair distribution of SMS capacity
- Unused daily quota from previous day carries over to next day (within same month)
- System automatically switches to fallback provider when daily limit is reached

**Impact on E-KOLEK:**
- ✅ No action required - automatic failover ensures uninterrupted service
- ✅ Users will continue to receive OTP and notification SMS
- ✅ Service reliability maintained even during high-volume periods

---

## 📱 Sender Name Changes

### Daily Limit Active (Normal Operation)

When the daily limit has NOT been exceeded, messages use these sender names:

| Message Type | Sender Name | Usage in E-KOLEK | Network Support |
|--------------|-------------|------------------|-----------------|
| **OTP Messages** | `iprogOTP` | OTP verification codes | Globe, TM |
| **Regular Messages** | `iprogSMS` | Notifications, alerts | Globe, TM |
| **Reminders** | `iprogRemind` | Scheduled reminders | Globe, TM |

**⚠️ Network Limitation:** These sender names do NOT support Smart/TNT networks.

### Fallback Mode (Daily Limit Exceeded)

When the daily limit is reached, all messages automatically use:

| Sender Name | Network Support | Auto-Activation |
|-------------|-----------------|-----------------|
| `iprogtech` | Globe, TM (NOT Smart/TNT) | ✅ Automatic |

**Note:** The fallback sender name also does not support Smart/TNT networks.

---

## 🔄 Automatic Fallback System

### How It Works

```
┌─────────────────────────┐
│  Send SMS Request       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Check Daily Limit      │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌─────────┐   ┌──────────┐
│ Within  │   │ Exceeded │
│ Limit   │   │ Limit    │
└────┬────┘   └─────┬────┘
     │              │
     ▼              ▼
┌─────────┐   ┌──────────┐
│iprogOTP │   │iprogtech │
│iprogSMS │   │(Fallback)│
└─────────┘   └──────────┘
     │              │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────┐
│  SMS Delivered          │
└─────────────────────────┘
```

### Benefits

✅ **No Service Interruption:** Messages continue to be sent even when daily limit is reached
✅ **Automatic Switching:** No manual intervention required
✅ **Transparent to Users:** Users receive SMS regardless of provider status
✅ **Cost Optimization:** Daily limits help manage SMS costs effectively

---

## 💻 Code Changes Implemented

### 1. OTP Service (`accounts/otp_service.py`)

**Before:**
```python
'sender_name': 'Ka Prets'  # Temporary sender name
```

**After:**
```python
'sender_name': 'iprogOTP'  # OTP sender name (fallback: 'iprogtech')
```

**Impact:**
- OTP messages now use proper sender name `iprogOTP`
- Automatic fallback to `iprogtech` when daily limit exceeded
- Better message classification for end users

### 2. SMS Service (`accounts/sms_service.py`)

**Before:**
```python
'sender_name': 'Ka Prets'  # Temporary sender name
```

**After:**
```python
'sender_name': 'iprogSMS'  # Regular messages sender name (fallback: 'iprogtech')
```

**Impact:**
- Regular notification messages use `iprogSMS` sender name
- Consistent with API recommendations
- Automatic fallback support

---

## 📊 Monitoring & Troubleshooting

### Expected Behavior

**Normal Operation (Daily Limit Active):**
- OTP messages show sender: `iprogOTP`
- Notification messages show sender: `iprogSMS`
- Works on Globe and TM networks

**Fallback Mode (Daily Limit Exceeded):**
- All messages show sender: `iprogtech`
- Service continues without interruption
- Resets when daily quota is restored

### Troubleshooting

**Issue:** SMS not received
**Possible Causes:**
1. ❌ Smart/TNT network (not supported by current sender names)
2. ❌ Daily and monthly limits both exceeded (rare)
3. ❌ Invalid phone number format
4. ❌ Network issues on recipient's side

**Solution:**
1. Verify recipient is using Globe or TM network
2. Check SMS API logs for delivery status
3. Verify phone number format (639XXXXXXXXX)
4. Contact iProg SMS support if issue persists

### Log Messages to Monitor

**Successful Send (Daily Limit Active):**
```
✅ SMS sent successfully to 639XXXXXXXXX. Message ID: iSms-XXXXX
```

**Successful Send (Fallback Mode):**
```
✅ SMS sent successfully to 639XXXXXXXXX. Message ID: iSms-XXXXX
Note: Using fallback provider (sender: iprogtech)
```

**Failed Send:**
```
❌ SMS failed to 639XXXXXXXXX. Status: XXX, Error: [error message]
```

---

## 🔍 Network Support Summary

| Network | iprogOTP | iprogSMS | iprogRemind | iprogtech (Fallback) |
|---------|----------|----------|-------------|---------------------|
| **Globe** | ✅ | ✅ | ✅ | ✅ |
| **TM** | ✅ | ✅ | ✅ | ✅ |
| **Smart** | ❌ | ❌ | ❌ | ❌ |
| **TNT** | ❌ | ❌ | ❌ | ❌ |

**Important:** Current sender names do not support Smart/TNT networks. Users on these networks may not receive SMS messages.

---

## 📝 API Documentation

**Official API Endpoint:**
```
https://www.iprogsms.com/api/v1/sms_messages
```

**Request Parameters:**
```json
{
  "api_token": "your_api_token",
  "phone_number": "639XXXXXXXXX",
  "message": "Your message content",
  "sms_provider": 2,
  "sender_name": "iprogOTP"
}
```

**Response (Success):**
```json
{
  "success": true,
  "status": 200,
  "message": "Your SMS message has been successfully added to the queue...",
  "message_id": "iSms-XHYBk"
}
```

---

## ✅ Implementation Checklist

- [x] Updated `otp_service.py` sender name to `iprogOTP`
- [x] Updated `sms_service.py` sender name to `iprogSMS`
- [x] Added API update documentation to code comments
- [x] Updated class docstrings with API changes
- [x] Created comprehensive documentation file
- [ ] Test OTP sending on Globe network
- [ ] Test notification sending on TM network
- [ ] Monitor SMS delivery rates
- [ ] Update user documentation if needed

---

## 🎯 User Impact

### For Globe/TM Users
✅ **No Impact:** SMS delivery continues normally
✅ **Better Experience:** Proper sender names (iprogOTP, iprogSMS)
✅ **Reliable Service:** Automatic fallback ensures delivery

### For Smart/TNT Users
⚠️ **Limited Support:** Current sender names don't support Smart/TNT
⚠️ **Alternative:** Consider alternative OTP delivery method (email)
⚠️ **Future:** May require API provider to add Smart/TNT support

---

## 📞 Support & Contact

**iProg SMS Support:**
- Website: https://www.iprogsms.com
- API Documentation: https://www.iprogsms.com/api/v1/sms_messages

**E-KOLEK Development Team:**
- For issues with OTP delivery
- For questions about sender name behavior
- For Smart/TNT network support requests

---

## 📅 Version History

| Date | Version | Changes |
|------|---------|---------|
| Jan 14, 2026 | 2.0 | API update: Daily limit system, new sender names |
| Dec 23, 2025 | 1.1 | Temporary sender name: 'Ka Prets' |
| Earlier | 1.0 | Initial SMS integration |

---

**Status:** ✅ Implemented and Active
**Last Updated:** January 14, 2026
**Next Review:** Monitor for 30 days, evaluate Smart/TNT support needs
