"""
Comprehensive API endpoint testing script.
Tests all endpoints and reports errors.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.refresh_token = None
        self.results = []
        
    def log(self, endpoint, method, status, response_data, error=None):
        """Log test result."""
        result = {
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'success': 200 <= status < 300,
            'error': error,
            'response': response_data
        }
        self.results.append(result)
        
        status_icon = "✓" if result['success'] else "✗"
        print(f"{status_icon} {method} {endpoint} - {status}")
        if error:
            print(f"  Error: {error}")
    
    def test_endpoint(self, method, endpoint, data=None, files=None, auth=True):
        """Test a single endpoint."""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            self.log(endpoint, method, response.status_code, response_data)
            return response
            
        except Exception as e:
            self.log(endpoint, method, 0, None, str(e))
            return None
    
    def test_authentication(self):
        """Test authentication endpoints."""
        print("\n=== Testing Authentication ===")
        
        # Register
        register_data = {
            'username': f'testuser_{datetime.now().timestamp()}',
            'email': f'test_{datetime.now().timestamp()}@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.test_endpoint('POST', '/api/users/register/', register_data, auth=False)
        
        # Save token and user info from registration
        if response and response.status_code == 201:
            data = response.json()
            self.token = data.get('tokens', {}).get('access')
            self.refresh_token = data.get('tokens', {}).get('refresh')
            self.test_user_id = data.get('user', {}).get('id')
            self.test_username = data.get('user', {}).get('username')
            if self.token:
                print(f"  ✓ Got token from registration")
                print(f"  ✓ Test user ID: {self.test_user_id}")
        
        # Try login with the newly created user
        if hasattr(self, 'test_username'):
            login_data = {
                'username': self.test_username,
                'password': 'TestPass123!'
            }
            response = self.test_endpoint('POST', '/api/token/', login_data, auth=False)
            if response and response.status_code == 200:
                print(f"  ✓ Login successful")
        
        # Token refresh
        if self.refresh_token:
            self.test_endpoint('POST', '/api/token/refresh/', {'refresh': self.refresh_token}, auth=False)
    
    def test_users(self):
        """Test user endpoints."""
        print("\n=== Testing Users ===")
        
        self.test_endpoint('GET', '/api/users/')
        self.test_endpoint('GET', '/api/users/me/')
        
        # Use the test user's own ID
        if hasattr(self, 'test_user_id'):
            self.test_endpoint('GET', f'/api/users/{self.test_user_id}/')
            self.test_endpoint('PATCH', f'/api/users/{self.test_user_id}/', {'bio': 'Updated bio'})
    
    def test_posts(self):
        """Test post endpoints."""
        print("\n=== Testing Posts ===")
        
        self.test_endpoint('GET', '/api/posts/')
        
        # Create a post with caption only (image is optional for testing)
        response = self.test_endpoint('POST', '/api/posts/', {
            'caption': 'Test post from API test',
            'location': 'Test Location'
        })
        
        # Save the created post ID
        if response and response.status_code == 201:
            self.test_post_id = response.json().get('id')
            print(f"  ✓ Created post ID: {self.test_post_id}")
        
        # Use existing post or created post
        post_id = getattr(self, 'test_post_id', 1)
        self.test_endpoint('GET', f'/api/posts/{post_id}/')
        self.test_endpoint('PATCH', f'/api/posts/{post_id}/', {'caption': 'Updated caption'})
        self.test_endpoint('POST', f'/api/posts/{post_id}/like/')
        # Use correct nested router URL for comments
        self.test_endpoint('POST', f'/api/posts/{post_id}/comments/', {'text': 'Test comment'})
    
    def test_stories(self):
        """Test story endpoints."""
        print("\n=== Testing Stories ===")
        
        self.test_endpoint('GET', '/api/stories/')
        
        # Create a story
        response = self.test_endpoint('POST', '/api/stories/', {
            'caption': 'Test story from API test'
        })
        
        # Save the created story ID
        if response and response.status_code == 201:
            self.test_story_id = response.json().get('id')
            print(f"  ✓ Created story ID: {self.test_story_id}")
            # Test getting the created story
            self.test_endpoint('GET', f'/api/stories/{self.test_story_id}/')
    
    def test_reels(self):
        """Test reel endpoints."""
        print("\n=== Testing Reels ===")
        
        self.test_endpoint('GET', '/api/reels/')
        
        # Create dummy video
        with open('test_video.mp4', 'wb') as f:
            f.write(b'fake video content')

        # Create a reel with video
        with open('test_video.mp4', 'rb') as video_file:
            files = {'video': ('test_video.mp4', video_file, 'video/mp4')}
            response = self.test_endpoint('POST', '/api/reels/', {
                'caption': 'Test reel from API test',
                'audio': 'Original Audio'
            }, files=files)
        
        # Get first available reel
        reels_response = self.test_endpoint('GET', '/api/reels/')
        if reels_response and reels_response.status_code == 200:
            reels_data = reels_response.json()
            if reels_data.get('results') and len(reels_data['results']) > 0:
                reel_id = reels_data['results'][0]['id']
                self.test_endpoint('GET', f'/api/reels/{reel_id}/')
                print(f"  ✓ Testing with reel ID: {reel_id}")
    
    def test_chat(self):
        """Test chat endpoints."""
        print("\n=== Testing Chat ===")
        
        self.test_endpoint('GET', '/api/chat/chats/')
        self.test_endpoint('GET', '/api/chat/messages/')
    
    def test_notifications(self):
        """Test notification endpoints."""
        print("\n=== Testing Notifications ===")
        
        self.test_endpoint('GET', '/api/notifications/')
        self.test_endpoint('GET', '/api/notifications/unread-count/')
        self.test_endpoint('PUT', '/api/notifications/mark-all-read/')
    
    def test_media(self):
        """Test media endpoints."""
        print("\n=== Testing Media ===")
        
        self.test_endpoint('GET', '/api/media/')
        self.test_endpoint('GET', '/api/media/stats/')
    
    def test_security(self):
        """Test security endpoints."""
        print("\n=== Testing Security ===")
        
        self.test_endpoint('GET', '/api/security/2fa/')
    
    def test_explore(self):
        """Test explore endpoints."""
        print("\n=== Testing Explore ===")
        
        self.test_endpoint('GET', '/api/explore/')
    
    def generate_report(self):
        """Generate test report."""
        print("\n" + "="*50)
        print("TEST REPORT")
        print("="*50)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['success'])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\n=== FAILED TESTS ===")
            for result in self.results:
                if not result['success']:
                    print(f"\n{result['method']} {result['endpoint']}")
                    print(f"  Status: {result['status']}")
                    if result['error']:
                        print(f"  Error: {result['error']}")
                    if result['response']:
                        print(f"  Response: {result['response']}")
        
        # Save to file
        with open('api_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        print("\nResults saved to api_test_results.json")
    
    def run_all_tests(self):
        """Run all tests."""
        print("Starting API Tests...")
        print(f"Base URL: {self.base_url}")
        
        self.test_authentication()
        self.test_users()
        self.test_posts()
        self.test_stories()
        self.test_reels()
        self.test_chat()
        self.test_notifications()
        self.test_media()
        self.test_security()
        self.test_explore()
        
        self.generate_report()


if __name__ == '__main__':
    tester = APITester()
    tester.run_all_tests()
