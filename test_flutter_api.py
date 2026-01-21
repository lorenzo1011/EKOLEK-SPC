"""
API Endpoint Testing Script for Flutter Mobile App
Tests all critical endpoints to ensure data fetching works correctly
Run this before the presentation to verify everything is working
"""

import requests
import json
from datetime import datetime

# ⚠️ UPDATE THIS WITH YOUR RAILWAY URL
BASE_URL = "https://your-app.railway.app"

# Test credentials - UPDATE with valid user
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_section(title):
    print(f"\n{BLUE}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}\n")

# Test results tracker
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def test_endpoint(name, method, url, headers=None, data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            print_error(f"Unsupported method: {method}")
            return None
        
        if response.status_code == expected_status:
            print_success(f"{name}: {response.status_code}")
            test_results["passed"] += 1
            return response
        else:
            print_error(f"{name}: Expected {expected_status}, got {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            test_results["failed"] += 1
            return None
            
    except requests.exceptions.Timeout:
        print_error(f"{name}: Request timeout")
        test_results["failed"] += 1
        return None
    except requests.exceptions.ConnectionError:
        print_error(f"{name}: Connection error - Check if backend is running")
        test_results["failed"] += 1
        return None
    except Exception as e:
        print_error(f"{name}: {str(e)}")
        test_results["failed"] += 1
        return None

def main():
    print_section("E-KOLEK API TESTING - Flutter Mobile App")
    print_info(f"Testing backend: {BASE_URL}")
    print_info(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ====================
    # TEST 1: LOGIN
    # ====================
    print_section("TEST 1: Authentication")
    
    login_response = test_endpoint(
        "Login Endpoint",
        "POST",
        f"{BASE_URL}/api/login/",
        headers={"Content-Type": "application/json"},
        data={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )
    
    if not login_response:
        print_error("LOGIN FAILED - Cannot proceed with other tests")
        print_error("Please verify:")
        print_error("1. Backend URL is correct")
        print_error("2. Test credentials are valid")
        print_error("3. Backend is running on Railway")
        return
    
    login_data = login_response.json()
    
    # Check OTP status
    if login_data.get('otp_bypassed'):
        print_success("OTP is DISABLED - Single-step login ✓")
        token = login_data.get('token')
        auth_header = f"Token {token}"
        print_info(f"DRF Token received: {token[:20]}...")
    elif login_data.get('otp_sent'):
        print_warning("OTP is ENABLED - Two-step login required")
        print_warning("This means Flutter app will need OTP verification screen")
        test_results["warnings"] += 1
        print_error("Cannot proceed with endpoint tests without OTP verification")
        return
    else:
        print_error("Unknown login response format")
        print_error(json.dumps(login_data, indent=2))
        return
    
    # Verify response structure
    print_info("Checking login response structure...")
    
    required_fields = ['success', 'token', 'user_info']
    for field in required_fields:
        if field in login_data:
            print_success(f"  ✓ {field} present")
        else:
            print_error(f"  ✗ {field} missing")
            test_results["warnings"] += 1
    
    if 'user_info' in login_data:
        user_info = login_data['user_info']
        user_fields = ['id', 'username', 'full_name', 'total_points', 'status']
        for field in user_fields:
            if field in user_info:
                print_success(f"    ✓ user_info.{field}: {user_info[field]}")
    
    # ====================
    # TEST 2: TOKEN VALIDATION
    # ====================
    print_section("TEST 2: Token Validation")
    
    test_endpoint(
        "Validate Token",
        "GET",
        f"{BASE_URL}/api/validate-token/",
        headers={"Authorization": auth_header}
    )
    
    # ====================
    # TEST 3: USER DATA ENDPOINTS
    # ====================
    print_section("TEST 3: User Data Endpoints")
    
    # Current user data
    user_data_response = test_endpoint(
        "Get Current User Data",
        "GET",
        f"{BASE_URL}/api/current_user_data/",
        headers={"Authorization": auth_header}
    )
    
    if user_data_response:
        user_data = user_data_response.json()
        if user_data.get('success'):
            print_success(f"  User ID: {user_data.get('user_info', {}).get('id', 'N/A')}")
            print_success(f"  Username: {user_data.get('user_info', {}).get('username', 'N/A')}")
            print_success(f"  Points: {user_data.get('user_info', {}).get('total_points', 0)}")
    
    # Current points
    points_response = test_endpoint(
        "Get Current Points",
        "GET",
        f"{BASE_URL}/api/current_points/",
        headers={"Authorization": auth_header}
    )
    
    if points_response:
        points_data = points_response.json()
        if points_data.get('success'):
            print_success(f"  Total Points: {points_data.get('user_points', {}).get('total_points', 0)}")
            print_success(f"  Family Points: {points_data.get('family_points', {}).get('total_family_points', 0)}")
    
    # Family members
    family_response = test_endpoint(
        "Get Family Members",
        "GET",
        f"{BASE_URL}/api/family_members/",
        headers={"Authorization": auth_header}
    )
    
    if family_response:
        family_data = family_response.json()
        if family_data.get('success'):
            member_count = len(family_data.get('family_members', []))
            print_success(f"  Family Members: {member_count}")
            print_success(f"  Family Name: {family_data.get('family_summary', {}).get('family_name', 'N/A')}")
    
    # ====================
    # TEST 4: SCHEDULE ENDPOINTS
    # ====================
    print_section("TEST 4: Schedule Endpoints")
    
    test_endpoint(
        "Get Garbage Schedule",
        "GET",
        f"{BASE_URL}/api/schedule/",
        headers={"Authorization": auth_header}
    )
    
    test_endpoint(
        "Get Today's Schedule",
        "GET",
        f"{BASE_URL}/api/schedule/today/",
        headers={"Authorization": auth_header}
    )
    
    test_endpoint(
        "Get All Schedules",
        "GET",
        f"{BASE_URL}/api/schedule/all/",
        headers={"Authorization": auth_header}
    )
    
    # ====================
    # TEST 5: GAME ENDPOINTS
    # ====================
    print_section("TEST 5: Game Endpoints")
    
    game_config_response = test_endpoint(
        "Get Game Configurations",
        "GET",
        f"{BASE_URL}/api/game/configurations/",
        headers={"Authorization": auth_header}
    )
    
    if game_config_response:
        game_data = game_config_response.json()
        if game_data.get('success'):
            print_success(f"  Quiz Cooldown: {game_data.get('quiz', {}).get('cooldown_hours', 0)} hours")
            print_success(f"  Drag-Drop Cooldown: {game_data.get('drag_drop', {}).get('cooldown_hours', 0)} hours")
    
    test_endpoint(
        "Get Quiz Cooldown",
        "GET",
        f"{BASE_URL}/api/game/cooldown/quiz/",
        headers={"Authorization": auth_header}
    )
    
    # ====================
    # TEST 6: NOTIFICATION ENDPOINTS
    # ====================
    print_section("TEST 6: Notification Endpoints")
    
    notifications_response = test_endpoint(
        "Get Notifications",
        "GET",
        f"{BASE_URL}/api/notifications/",
        headers={"Authorization": auth_header}
    )
    
    if notifications_response:
        notif_data = notifications_response.json()
        if notif_data.get('success'):
            notif_count = len(notif_data.get('notifications', []))
            print_success(f"  Total Notifications: {notif_count}")
    
    test_endpoint(
        "Get Unread Count",
        "GET",
        f"{BASE_URL}/api/notifications/unread-count/",
        headers={"Authorization": auth_header}
    )
    
    # ====================
    # TEST 7: LOGOUT
    # ====================
    print_section("TEST 7: Logout")
    
    test_endpoint(
        "Logout",
        "POST",
        f"{BASE_URL}/api/logout/",
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json"
        },
        data={}
    )
    
    # ====================
    # SUMMARY
    # ====================
    print_section("TEST SUMMARY")
    
    total_tests = test_results["passed"] + test_results["failed"]
    
    print(f"Total Tests Run: {total_tests}")
    print_success(f"Passed: {test_results['passed']}")
    
    if test_results["failed"] > 0:
        print_error(f"Failed: {test_results['failed']}")
    else:
        print_success("Failed: 0")
    
    if test_results["warnings"] > 0:
        print_warning(f"Warnings: {test_results['warnings']}")
    
    success_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print_success("\n🎉 ALL TESTS PASSED - READY FOR PRESENTATION!")
    elif success_rate >= 80:
        print_warning("\n⚠️  MOST TESTS PASSED - Check failures above")
    else:
        print_error("\n❌ CRITICAL FAILURES - NOT READY FOR PRESENTATION")
        print_error("Please fix the issues above before presenting")
    
    print(f"\n{BLUE}Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  E-KOLEK API TESTING SCRIPT")
    print("  Tests all endpoints for Flutter mobile app")
    print("="*60 + "\n")
    
    print_warning("IMPORTANT: Update these values in the script:")
    print(f"  BASE_URL = {BASE_URL}")
    print(f"  TEST_USERNAME = {TEST_USERNAME}")
    print(f"  TEST_PASSWORD = {TEST_PASSWORD}")
    
    response = input("\nHave you updated the values? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print_error("\nPlease update BASE_URL, TEST_USERNAME, and TEST_PASSWORD in the script first!")
        exit(1)
    
    main()
