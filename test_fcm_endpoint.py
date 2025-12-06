"""
Test script to check the FCM token endpoint.
"""
import requests
import json

# Configuration
BASE_URL = "http://192.168.11.107:8000"
USERNAME = "user1"  # Replace with actual username
PASSWORD = "TestPass123!"  # Replace with actual password

def get_auth_token():
    """Get JWT token for authentication."""
    url = f"{BASE_URL}/api/users/login/"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_add_fcm_token(token):
    """Test adding FCM token."""
    url = f"{BASE_URL}/api/notifications/preferences/add-fcm-token/"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "token": "test_fcm_token_12345"
    }
    
    print(f"\nTesting POST {url}")
    print(f"Headers: {headers}")
    print(f"Data: {data}")
    
    response = requests.post(url, headers=headers, json=data)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text}")
    
    return response

if __name__ == "__main__":
    print("Getting authentication token...")
    auth_token = get_auth_token()
    
    if auth_token:
        print(f"Got token: {auth_token[:20]}...")
        test_add_fcm_token(auth_token)
    else:
        print("Failed to get authentication token")
