"""
Test script to verify the new features
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_registration():
    """Test user registration"""
    print("\n✓ Testing registration...")
    payload = {
        "email": "testuser@mergington.edu",
        "password": "password123",
        "full_name": "Test User",
        "grade_level": 10
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ User registered: {data['email']}")
        return data
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_login():
    """Test user login"""
    print("\n✓ Testing login...")
    payload = {
        "email": "testuser@mergington.edu",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=payload)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print(f"  ✓ Login successful, token received")
        print(f"  ✓ User: {data['user']['full_name']}")
        return token
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_get_activities(token):
    """Test getting activities list"""
    print("\n✓ Testing get activities...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/activities", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        activities = response.json()
        print(f"  ✓ Retrieved {len(activities)} activities")
        if activities:
            print(f"  - {activities[0]['name']}: {activities[0]['description'][:50]}...")
        return activities
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_signup_activity(token, activity_id):
    """Test signing up for an activity"""
    print(f"\n✓ Testing activity signup (ID: {activity_id})...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/activities/{activity_id}/signup", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Successfully signed up for {data['activity']['name']}")
        return True
    else:
        print(f"  ✗ Error: {response.json()}")
        return False

def test_my_activities(token):
    """Test getting user's activities"""
    print("\n✓ Testing get my activities...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/my-activities", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        activities = response.json()
        print(f"  ✓ User is signed up for {len(activities)} activities")
        return activities
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_get_current_user(token):
    """Test getting current user profile"""
    print("\n✓ Testing get current user...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"  ✓ User: {user['full_name']} ({user['email']})")
        print(f"  ✓ Role: {user['role']}")
        return user
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_get_stats(token):
    """Test getting user statistics"""
    print("\n✓ Testing get stats...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/stats/my-activities", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"  ✓ Total activities signed up: {stats['total_activities']}")
        print(f"  ✓ Activities attended: {stats['attended_activities']}")
        return stats
    else:
        print(f"  ✗ Error: {response.json()}")
        return None

def test_unregister_activity(token, activity_id):
    """Test unregistering from activity"""
    print(f"\n✓ Testing unregister from activity (ID: {activity_id})...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/activities/{activity_id}/unregister", headers=headers)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  ✓ Successfully unregistered")
        return True
    else:
        print(f"  ✗ Error: {response.json()}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Mergington High School Activities API")
    print("=" * 60)
    
    # Test registration
    user = test_registration()
    
    # Test login
    token = test_login()
    if not token:
        exit(1)
    
    # Test getting activities
    activities = test_get_activities(token)
    if not activities:
        exit(1)
    
    # Test signing up for an activity
    activity_id = activities[0]['id']
    test_signup_activity(token, activity_id)
    
    # Test getting my activities
    test_my_activities(token)
    
    # Test getting current user
    test_get_current_user(token)
    
    # Test getting stats
    test_get_stats(token)
    
    # Test unregistering
    test_unregister_activity(token, activity_id)
    
    # Verify unregistered
    test_my_activities(token)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
