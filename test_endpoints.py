"""
PittState-Connect API v1 Smoke Tests
Tests critical endpoints to verify system functionality.
"""

import requests
import json
from loguru import logger

# Test configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (from seed data)
ADMIN_EMAIL = "admin@pittstate.edu"
ADMIN_PASSWORD = "AdminPassword123!"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.passed = 0
        self.failed = 0
        
    def test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Execute a single test."""
        
        url = f"{API_BASE}{endpoint}"
        logger.info(f"🧪 Testing: {name}")
        logger.info(f"   {method} {url}")
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                logger.info(f"✅ PASSED: Status {response.status_code}")
                if response.headers.get("Content-Type", "").startswith("application/json"):
                    logger.info(f"   Response: {json.dumps(response.json(), indent=2)[:200]}...")
                self.passed += 1
                return response
            else:
                logger.error(f"❌ FAILED: Expected {expected_status}, got {response.status_code}")
                logger.error(f"   Response: {response.text[:500]}")
                self.failed += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ FAILED: {e}")
            self.failed += 1
            return None
    
    def login(self):
        """Login as admin and store session."""
        
        logger.info("🔐 Logging in as admin...")
        
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            data={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            allow_redirects=False
        )
        
        if response.status_code in [200, 302]:
            logger.info("✅ Login successful")
            return True
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            return False
    
    def run_health_checks(self):
        """Test health and metrics endpoints."""
        
        logger.info("\n📊 Health & Metrics Tests")
        logger.info("=" * 60)
        
        self.test("Health Check", "GET", "/health")
        self.test("Metrics Export", "GET", "/metrics")
    
    def run_feature_flag_tests(self):
        """Test feature flag endpoints."""
        
        logger.info("\n🚩 Feature Flag Tests")
        logger.info("=" * 60)
        
        # List all flags
        self.test("List Feature Flags", "GET", "/feature-flags")
        
        # Check specific flag
        self.test("Check AI Assistant Flag", "GET", "/feature-flags/ai_assistant/check")
        
        # Create new flag
        new_flag = {
            "name": "test_feature",
            "description": "Test feature for smoke tests",
            "enabled": True,
            "rollout_percentage": 50
        }
        response = self.test("Create Feature Flag", "POST", "/feature-flags", data=new_flag)
        
        # Update flag
        if response:
            update_data = {"enabled": False}
            self.test("Update Feature Flag", "PUT", "/feature-flags/test_feature", data=update_data)
        
        # Delete flag
        self.test("Delete Feature Flag", "DELETE", "/feature-flags/test_feature")
    
    def run_ab_test_tests(self):
        """Test A/B testing endpoints."""
        
        logger.info("\n🧪 A/B Testing Tests")
        logger.info("=" * 60)
        
        # List A/B tests
        self.test("List A/B Tests", "GET", "/ab-tests")
        
        # Get variant assignment
        self.test("Get A/B Variant", "GET", "/ab-tests/scholarship_matching_algorithm/variant")
        
        # Get test results
        self.test("Get A/B Results", "GET", "/ab-tests/scholarship_matching_algorithm/results")
    
    def run_notification_tests(self):
        """Test notification endpoints."""
        
        logger.info("\n🔔 Notification Tests")
        logger.info("=" * 60)
        
        # Get preferences
        self.test("Get Notification Preferences", "GET", "/notifications/preferences")
        
        # Update preferences
        prefs_update = {
            "notification_type": "new_post",
            "enabled": True,
            "channels": ["in_app", "email"]
        }
        self.test("Update Notification Preferences", "PUT", "/notifications/preferences", data=prefs_update)
        
        # List notifications
        self.test("List Notifications", "GET", "/notifications")
        
        # Get stats
        self.test("Get Notification Stats", "GET", "/notifications/stats")
    
    def run_data_governance_tests(self):
        """Test data governance endpoints."""
        
        logger.info("\n🗂️ Data Governance Tests")
        logger.info("=" * 60)
        
        # Track lineage
        lineage_data = {
            "entity_type": "scholarship_application",
            "entity_id": "test-123",
            "operation": "create",
            "actor_id": 1,
            "metadata": {"source": "api_test"}
        }
        self.test("Track Data Lineage", "POST", "/data-governance/lineage", data=lineage_data)
        
        # Get lineage
        self.test("Get Lineage Chain", "GET", "/data-governance/lineage/scholarship_application/test-123")
        
        # Get bias report
        self.test("Get Bias Monitoring Report", "GET", "/data-governance/bias/scholarship_predictor")
        
        # Data quality check
        quality_data = {
            "entity_type": "user",
            "checks": ["completeness", "validity"]
        }
        self.test("Run Data Quality Check", "POST", "/data-governance/quality", data=quality_data)
    
    def run_analytics_tests(self):
        """Test analytics endpoints."""
        
        logger.info("\n📈 Analytics Tests")
        logger.info("=" * 60)
        
        # Dashboard
        self.test("Get Analytics Dashboard", "GET", "/analytics/dashboard")
        
        # Insights
        self.test("Get Analytics Insights", "GET", "/analytics/insights")
        
        # Real-time stats
        self.test("Get Real-time Stats", "GET", "/analytics/realtime")
    
    def run_monetization_tests(self):
        """Test monetization endpoints."""
        
        logger.info("\n💰 Monetization Tests")
        logger.info("=" * 60)
        
        # Subscription tiers
        self.test("Get Subscription Tiers", "GET", "/subscriptions/tiers")
        
        # Tier details
        self.test("Get Silver Tier Info", "GET", "/subscriptions/tiers/silver")
        
        # My subscription
        self.test("Get My Subscription", "GET", "/subscriptions/my")
        
        # Check benefit
        self.test("Check Analytics Benefit", "GET", "/subscriptions/benefits/analytics_access")
        
        # Sponsorship packages
        self.test("Get Sponsorship Packages", "GET", "/sponsorships/packages")
        
        # Revenue report (admin)
        self.test("Get Revenue Report", "GET", "/monetization/revenue?days=30")
        
        # Subscription stats (admin)
        self.test("Get Subscription Stats", "GET", "/monetization/subscriptions/stats")
    
    def print_summary(self):
        """Print test summary."""
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info(f"✅ Passed: {self.passed}")
        logger.info(f"❌ Failed: {self.failed}")
        logger.info(f"📊 Total:  {total}")
        logger.info(f"🎯 Pass Rate: {pass_rate:.1f}%")
        
        if self.failed == 0:
            logger.info("\n🎉 All tests passed! System is operational.")
        else:
            logger.warning(f"\n⚠️ {self.failed} test(s) failed. Review logs above.")
        
        logger.info("=" * 60)

def main():
    """Run all smoke tests."""
    
    logger.info("🚀 Starting PittState-Connect API v1 Smoke Tests")
    logger.info("=" * 60)
    logger.info(f"Base URL: {BASE_URL}")
    logger.info(f"API URL: {API_BASE}")
    logger.info("=" * 60)
    
    tester = APITester()
    
    # Login first
    if not tester.login():
        logger.error("❌ Cannot proceed without authentication")
        return False
    
    # Run all test suites
    tester.run_health_checks()
    tester.run_feature_flag_tests()
    tester.run_ab_test_tests()
    tester.run_notification_tests()
    tester.run_data_governance_tests()
    tester.run_analytics_tests()
    tester.run_monetization_tests()
    
    # Print summary
    tester.print_summary()
    
    return tester.failed == 0

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
