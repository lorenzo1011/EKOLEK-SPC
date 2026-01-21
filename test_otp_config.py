"""
Test OTP Configuration
Tests the backend OTP bypass functionality for mobile app login
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
django.setup()

from django.conf import settings
import requests
import json

def test_otp_config():
    """Test OTP configuration setting"""
    print("\n" + "="*60)
    print("🔍 OTP CONFIGURATION TEST")
    print("="*60)
    
    # Check the setting
    otp_enabled = settings.OTP_VERIFICATION_ENABLED
    print(f"\n✅ OTP_VERIFICATION_ENABLED = {otp_enabled}")
    print(f"   Type: {type(otp_enabled)}")
    
    # Check environment variable
    env_value = os.environ.get('OTP_VERIFICATION_ENABLED', 'NOT SET')
    print(f"\n🌍 Environment Variable:")
    print(f"   OTP_VERIFICATION_ENABLED = '{env_value}'")
    
    if otp_enabled:
        print("\n❌ OTP IS ENABLED - Mobile login will require OTP")
        print("   To disable: Set Railway variable OTP_VERIFICATION_ENABLED = False")
    else:
        print("\n✅ OTP IS DISABLED - Mobile login will bypass OTP and return token directly")
    
    return otp_enabled

def test_login_endpoint(base_url="http://localhost:8000"):
    """Test the login endpoint"""
    print("\n" + "="*60)
    print("🔧 LOGIN ENDPOINT TEST")
    print("="*60)
    
    print(f"\nTesting: {base_url}/api/login/")
    
    # Test login
    test_credentials = {
        "username": "test_user",
        "password": "test_password"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/login/",
            json=test_credentials,
            timeout=5
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        print(f"📄 Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        data = response.json()
        
        # Check response format
        if "otp_bypassed" in data and data.get("otp_bypassed") == True:
            print("\n✅ SUCCESS: OTP bypassed, token returned!")
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
            print(f"   User: {data.get('user_info', {}).get('username', 'N/A')}")
            return True
        elif "otp_sent" in data:
            print("\n❌ FAILURE: OTP still enabled, no token returned")
            print("   Backend is sending OTP instead of bypassing it")
            print("   Check Railway environment variable: OTP_VERIFICATION_ENABLED = False")
            return False
        elif "token" in data:
            print("\n✅ SUCCESS: Token returned!")
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
            return True
        else:
            print("\n⚠️  Unexpected response format")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n⚠️  Cannot connect to {base_url}")
        print("   Make sure the server is running")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def main():
    print("\n" + "="*60)
    print("🚀 KOLEK MOBILE LOGIN - OTP CONFIGURATION TEST")
    print("="*60)
    
    # Test 1: Check OTP configuration
    otp_enabled = test_otp_config()
    
    # Test 2: Test login endpoint
    print("\n")
    test_login_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)
    
    if not otp_enabled:
        print("\n✅ Backend Configuration: OTP DISABLED")
        print("   Expected Response: {'otp_bypassed': true, 'token': '...', 'user_info': {...}}")
        print("\n✅ Mobile app should:")
        print("   1. POST to /api/login/ with username/password")
        print("   2. Receive token immediately (no OTP screen)")
        print("   3. Save token for API requests")
    else:
        print("\n❌ Backend Configuration: OTP ENABLED")
        print("   Current Response: {'otp_sent': true, 'user_id': '...'}")
        print("\n🔧 TO FIX:")
        print("   1. Go to Railway Dashboard → Your Project")
        print("   2. Click 'Variables' tab")
        print("   3. Add: OTP_VERIFICATION_ENABLED = False")
        print("   4. Click 'Deploy' to redeploy with new variable")
        print("   5. Wait 2-3 minutes for deployment")
        print("   6. Test again: Mobile app should get token immediately")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
