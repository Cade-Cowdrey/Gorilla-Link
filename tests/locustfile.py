"""
Performance tests using Locust
Load testing for key endpoints
"""

try:
    from locust import HttpUser, task, between
    LOCUST_AVAILABLE = True
except ImportError:
    LOCUST_AVAILABLE = False
    print("locust not installed. Install with: pip install locust")
    # Create stub classes
    class HttpUser:
        pass
    def task(func):
        return func
    def between(min_wait, max_wait):
        return lambda: None

import random


class WebsiteUser(HttpUser):
    """Simulates a typical website user"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Login when user starts"""
        # Login with test credentials
        self.client.post("/auth/login", json={
            "email": "test@pittstate.edu",
            "password": "password123"
        })
    
    @task(10)
    def view_homepage(self):
        """View homepage - most common action"""
        self.client.get("/")
    
    @task(5)
    def view_jobs(self):
        """Browse job listings"""
        self.client.get("/careers/jobs")
    
    @task(3)
    def search_jobs(self):
        """Search for jobs"""
        keywords = ["software", "engineer", "data", "manager", "analyst"]
        keyword = random.choice(keywords)
        self.client.get(f"/careers/jobs/search?q={keyword}")
    
    @task(4)
    def view_events(self):
        """Browse events"""
        self.client.get("/events")
    
    @task(2)
    def view_profile(self):
        """View own profile"""
        self.client.get("/profile")
    
    @task(1)
    def view_analytics(self):
        """View analytics (admin)"""
        self.client.get("/analytics/api/overview")


class APIUser(HttpUser):
    """Simulates API client"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Authenticate API user"""
        response = self.client.post("/api/auth/login", json={
            "email": "test@pittstate.edu",
            "password": "password123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
        else:
            self.token = None
    
    @task(8)
    def api_list_jobs(self):
        """GET /api/jobs"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client.get("/api/jobs", headers=headers)
    
    @task(5)
    def api_get_job_detail(self):
        """GET /api/jobs/:id"""
        job_id = random.randint(1, 100)
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client.get(f"/api/jobs/{job_id}", headers=headers)
    
    @task(3)
    def api_search_jobs(self):
        """GET /api/jobs/search"""
        keywords = ["software", "engineer", "data", "manager"]
        keyword = random.choice(keywords)
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client.get(f"/api/jobs/search?q={keyword}", headers=headers)
    
    @task(4)
    def api_list_events(self):
        """GET /api/events"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client.get("/api/events", headers=headers)
    
    @task(2)
    def api_get_profile(self):
        """GET /api/profile"""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        self.client.get("/api/profile", headers=headers)


class HeavyUser(HttpUser):
    """Simulates heavy API usage (for rate limit testing)"""
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test rate limiting"""
        self.client.get("/api/jobs")
