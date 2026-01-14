"""
Test script to verify OTP rate limiting behavior
Tests that successful logins don't trigger rate limiting
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eko.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from accounts.otp_service import send_otp, verify_otp, clear_failed_login_attempts
from django.core.cache import cache

def test_successful_login_scenario():
    """
    Test: User logs in successfully 3 times
    Expected: OTP sending should NOT be locked
    """
    print("\n" + "="*80)
    print("TEST 1: Successful Login Scenario (3 successful logins)")
    print("="*80)
    
    test_phone = "639171234567"
    
    # Clear any existing data
    cache.clear()
    
    for i in range(1, 4):
        print(f"\n--- Attempt {i}/3 (Successful Login) ---")
        
        # Send OTP
        send_result = send_otp(test_phone)
        print(f"Send OTP Result: {send_result.get('success', False)}")
        
        if send_result.get('success'):
            otp_code = send_result.get('data', {}).get('otp_code')
            print(f"OTP Code: {otp_code}")
            
            # Verify OTP (simulating successful login)
            verify_result = verify_otp(test_phone, otp_code)
            print(f"Verify Result: {verify_result.get('success', False)}")
            print(f"Message: {verify_result.get('message', 'N/A')}")
        else:
            print(f"ERROR: {send_result.get('error')}")
            return False
    
    # Try to send OTP again after 3 successful logins
    print("\n--- Attempt 4 (Should NOT be blocked) ---")
    send_result = send_otp(test_phone)
    print(f"Send OTP Result: {send_result.get('success', False)}")
    
    if send_result.get('success'):
        print("✅ TEST PASSED: OTP sending is NOT blocked after 3 successful logins")
        return True
    else:
        print(f"❌ TEST FAILED: OTP sending blocked incorrectly: {send_result.get('error')}")
        return False


def test_failed_login_scenario():
    """
    Test: User has 3 failed login attempts
    Expected: OTP sending should be locked for 15 minutes
    """
    print("\n" + "="*80)
    print("TEST 2: Failed Login Scenario (3 failed logins)")
    print("="*80)
    
    test_phone = "639177654321"
    
    # Clear any existing data
    cache.clear()
    
    for i in range(1, 4):
        print(f"\n--- Attempt {i}/3 (Failed Login) ---")
        
        # Send OTP
        send_result = send_otp(test_phone)
        print(f"Send OTP Result: {send_result.get('success', False)}")
        
        if send_result.get('success'):
            # Use wrong OTP (simulating failed login)
            verify_result = verify_otp(test_phone, "000000")
            print(f"Verify Result: {verify_result.get('success', False)}")
            print(f"Error: {verify_result.get('error', 'N/A')}")
        else:
            print(f"ERROR: {send_result.get('error')}")
    
    # Try to send OTP again after 3 failed logins
    print("\n--- Attempt 4 (Should be BLOCKED) ---")
    send_result = send_otp(test_phone)
    print(f"Send OTP Result: {send_result.get('success', False)}")
    
    if not send_result.get('success') and 'failed login' in send_result.get('error', '').lower():
        print("✅ TEST PASSED: OTP sending is correctly blocked after 3 failed logins")
        print(f"   Reason: {send_result.get('error')}")
        return True
    else:
        print(f"❌ TEST FAILED: OTP should be blocked but wasn't")
        return False


def test_reset_on_successful_login():
    """
    Test: User has 2 failed attempts, then 1 successful login
    Expected: Counter should reset, user can continue logging in
    """
    print("\n" + "="*80)
    print("TEST 3: Counter Reset on Successful Login")
    print("="*80)
    
    test_phone = "639179999999"
    
    # Clear any existing data
    cache.clear()
    
    # 2 Failed attempts
    for i in range(1, 3):
        print(f"\n--- Failed Attempt {i}/2 ---")
        send_result = send_otp(test_phone)
        if send_result.get('success'):
            verify_otp(test_phone, "000000")  # Wrong OTP
    
    # 1 Successful login
    print(f"\n--- Successful Login (Should reset counter) ---")
    send_result = send_otp(test_phone)
    if send_result.get('success'):
        otp_code = send_result.get('data', {}).get('otp_code')
        verify_result = verify_otp(test_phone, otp_code)  # Correct OTP
        print(f"Verify Result: {verify_result.get('success', False)}")
    
    # Now try 3 more successful logins (should all work)
    print(f"\n--- 3 More Successful Logins (Counter was reset) ---")
    all_success = True
    for i in range(1, 4):
        send_result = send_otp(test_phone)
        if not send_result.get('success'):
            all_success = False
            print(f"❌ Failed at attempt {i}")
            break
        else:
            otp_code = send_result.get('data', {}).get('otp_code')
            verify_otp(test_phone, otp_code)
            print(f"✅ Attempt {i} successful")
    
    if all_success:
        print("\n✅ TEST PASSED: Counter was reset after successful login")
        return True
    else:
        print("\n❌ TEST FAILED: Counter was not reset properly")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("OTP RATE LIMITING TEST SUITE")
    print("Testing the fix for OTP rate limiting based on failed login attempts")
    print("="*80)
    
    results = []
    
    # Run all tests
    results.append(("Successful Login Scenario", test_successful_login_scenario()))
    results.append(("Failed Login Scenario", test_failed_login_scenario()))
    results.append(("Counter Reset on Success", test_reset_on_successful_login()))
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The OTP rate limiting fix is working correctly.")
    else:
        print("\n⚠️ SOME TESTS FAILED. Please review the implementation.")
