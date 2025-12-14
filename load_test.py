"""
Load testing script for finaleventmate
Tests the application with 500+ concurrent users
Run with: locust -f load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random


class EventMateUser(HttpUser):
    """
    Simulates a user browsing and interacting with the EventMate application
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - simulate login for some users"""
        # 30% of users will be logged in
        if random.random() < 0.3:
            self.login()
    
    def login(self):
        """Simulate user login"""
        response = self.client.get("/accounts/login/")
        csrftoken = response.cookies.get('csrftoken')
        
        self.client.post("/accounts/login/", {
            "username": f"testuser{random.randint(1, 100)}",
            "password": "testpass123",
            "csrfmiddlewaretoken": csrftoken
        })
    
    @task(10)
    def view_homepage(self):
        """Visit the homepage - most common action"""
        self.client.get("/")
    
    @task(8)
    def search_events(self):
        """Search for events"""
        search_terms = ["music", "sports", "tech", "food", "arts"]
        locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        
        params = {
            "q": random.choice(search_terms),
            "location": random.choice(locations)
        }
        self.client.get("/events/", params=params)
    
    @task(6)
    def view_event_detail(self):
        """View a specific event detail page"""
        # Simulate viewing events with different slugs
        event_id = random.randint(1, 50)
        self.client.get(f"/event/event-{event_id}/", name="/event/[slug]/")
    
    @task(3)
    def filter_by_category(self):
        """Filter events by category"""
        categories = ["music", "sports", "arts", "food", "business", "tech", "wellness"]
        self.client.get("/events/", params={"category": random.choice(categories)})
    
    @task(2)
    def view_city_events(self):
        """View events for a specific city"""
        cities = ["new-york", "los-angeles", "chicago", "houston", "phoenix"]
        self.client.get(f"/city/{random.choice(cities)}/", name="/city/[slug]/")
    
    @task(1)
    def view_my_bookings(self):
        """View my bookings (logged in users only)"""
        self.client.get("/my-bookings/")
    
    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health/")


class HostUser(HttpUser):
    """
    Simulates a host user managing events
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login as host"""
        response = self.client.get("/accounts/login/")
        csrftoken = response.cookies.get('csrftoken')
        
        self.client.post("/accounts/login/", {
            "username": f"host{random.randint(1, 20)}",
            "password": "hostpass123",
            "csrfmiddlewaretoken": csrftoken
        })
    
    @task(5)
    def view_my_events(self):
        """View hosted events"""
        self.client.get("/my-events/")
    
    @task(2)
    def view_event_detail(self):
        """View event details"""
        event_id = random.randint(1, 50)
        self.client.get(f"/event/event-{event_id}/", name="/event/[slug]/")
    
    @task(1)
    def view_create_event_page(self):
        """View create event form"""
        self.client.get("/create/")


class APIUser(HttpUser):
    """
    Simulates API/AJAX requests
    """
    wait_time = between(0.5, 2)
    
    @task(10)
    def search_autocomplete(self):
        """Test autocomplete search"""
        queries = ["mus", "spo", "new", "los", "chi"]
        self.client.get("/search/autocomplete/", params={"q": random.choice(queries)})
    
    @task(5)
    def metrics_endpoint(self):
        """Check metrics"""
        self.client.get("/metrics/")
    
    @task(3)
    def readiness_check(self):
        """Readiness probe"""
        self.client.get("/health/ready/")


# Performance test scenarios
class StressTest(HttpUser):
    """
    Stress test - simulates high load scenarios
    """
    wait_time = between(0.1, 0.5)  # Faster requests
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test performance"""
        endpoints = [
            "/",
            "/events/",
            "/health/",
            "/health/live/",
        ]
        self.client.get(random.choice(endpoints))