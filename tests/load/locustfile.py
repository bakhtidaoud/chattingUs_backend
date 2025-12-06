"""
Load testing with Locust.

Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random


class ChattingUsUser(HttpUser):
    """Simulated user for load testing."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Login when user starts."""
        # Register or login
        response = self.client.post("/api/token/", {
            "username": "testuser",
            "password": "testpass123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()['access']
            self.client.headers = {
                'Authorization': f'Bearer {self.token}'
            }
        else:
            # If login fails, try to register
            self.client.post("/api/users/register/", {
                "username": f"user{random.randint(1000, 9999)}",
                "email": f"user{random.randint(1000, 9999)}@example.com",
                "password": "testpass123!",
                "password2": "testpass123!"
            })
    
    @task(5)
    def view_feed(self):
        """View posts feed."""
        self.client.get("/api/posts/")
    
    @task(3)
    def view_profile(self):
        """View own profile."""
        self.client.get("/api/users/me/")
    
    @task(2)
    def view_stories(self):
        """View stories."""
        self.client.get("/api/stories/")
    
    @task(2)
    def view_reels(self):
        """View reels."""
        self.client.get("/api/reels/")
    
    @task(1)
    def create_post(self):
        """Create a new post."""
        self.client.post("/api/posts/", {
            "caption": f"Test post {random.randint(1, 10000)}"
        })
    
    @task(1)
    def like_post(self):
        """Like a random post."""
        post_id = random.randint(1, 100)
        self.client.post(f"/api/posts/{post_id}/like/")
    
    @task(1)
    def comment_on_post(self):
        """Comment on a random post."""
        post_id = random.randint(1, 100)
        self.client.post(f"/api/posts/{post_id}/comments/", {
            "text": f"Test comment {random.randint(1, 1000)}"
        })
    
    @task(1)
    def search_users(self):
        """Search for users."""
        query = random.choice(['test', 'user', 'admin'])
        self.client.get(f"/api/users/?search={query}")
    
    @task(1)
    def view_notifications(self):
        """View notifications."""
        self.client.get("/api/notifications/")


class AdminUser(HttpUser):
    """Simulated admin user for load testing."""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as admin."""
        response = self.client.post("/api/token/", {
            "username": "admin",
            "password": "admin123!"
        })
        
        if response.status_code == 200:
            self.token = response.json()['access']
            self.client.headers = {
                'Authorization': f'Bearer {self.token}'
            }
    
    @task(3)
    def view_reports(self):
        """View moderation reports."""
        self.client.get("/api/moderation/reports/")
    
    @task(2)
    def view_users(self):
        """View all users."""
        self.client.get("/api/users/")
    
    @task(1)
    def view_system_settings(self):
        """View system settings."""
        self.client.get("/api/system-settings/")
