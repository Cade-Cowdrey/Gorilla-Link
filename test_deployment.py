#!/usr/bin/env python3
"""
Comprehensive Deployment Test Suite for PittState-Connect
Tests all critical paths and verifies route fixes from deployment #31
"""

import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

# Test configuration
BASE_URL = "https://pittstate-connect.onrender.com"
TIMEOUT = 30

class LinkExtractor(HTMLParser):
    """Extract all links from HTML"""
    def __init__(self):
        super().__init__()
        self.links = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href':
                    self.links.append(value)

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []
    
    def add_pass(self, test_name, message=""):
        self.passed += 1
        self.details.append(f"✅ PASS: {test_name} {message}")
        print(f"✅ PASS: {test_name} {message}")
    
    def add_fail(self, test_name, error):
        self.failed += 1
        self.details.append(f"❌ FAIL: {test_name} - {error}")
        print(f"❌ FAIL: {test_name} - {error}")
    
    def add_warning(self, test_name, message):
        self.warnings += 1
        self.details.append(f"⚠️  WARN: {test_name} - {message}")
        print(f"⚠️  WARN: {test_name} - {message}")
    
    def summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Passed:   {self.passed}")
        print(f"Total Failed:   {self.failed}")
        print(f"Total Warnings: {self.warnings}")
        print(f"Success Rate:   {self.passed/(self.passed+self.failed)*100:.1f}%")
        print("="*70)
        return self.failed == 0

def test_url(url, test_name, results, check_redirect=False):
    """Test a single URL endpoint"""
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req, timeout=TIMEOUT)
        status = response.status
        
        if status == 200:
            results.add_pass(test_name, f"(Status: {status})")
            return response.read().decode('utf-8', errors='ignore')
        elif 300 <= status < 400:
            if check_redirect:
                results.add_pass(test_name, f"(Redirect: {status})")
            else:
                results.add_warning(test_name, f"Redirected (Status: {status})")
            return None
        else:
            results.add_warning(test_name, f"Unexpected status: {status}")
            return None
            
    except HTTPError as e:
        if e.code == 401:
            results.add_pass(test_name, "(401 - Auth required, route exists)")
            return None
        elif e.code == 404:
            results.add_fail(test_name, "404 Not Found - Route missing")
            return None
        elif e.code == 500:
            results.add_fail(test_name, "500 Server Error - Check logs")
            return None
        else:
            results.add_fail(test_name, f"HTTP {e.code}: {e.reason}")
            return None
    except URLError as e:
        results.add_fail(test_name, f"Connection error: {e.reason}")
        return None
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {str(e)}")
        return None

def main():
    results = TestResults()
    
    print("="*70)
    print("PITTSTATE-CONNECT DEPLOYMENT #31 TEST SUITE")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Testing deployment fixes for 18 template files...")
    print("="*70 + "\n")
    
    # 1. TEST HOMEPAGE & CORE ROUTES
    print("\n📍 TEST 1: HOMEPAGE & CORE ROUTES")
    print("-"*70)
    
    homepage_html = test_url(f"{BASE_URL}/", "Homepage (/)", results)
    
    if homepage_html:
        # Check for BuildError in response
        if "BuildError" in homepage_html or "Could not build url" in homepage_html:
            results.add_fail("Homepage BuildError Check", "BuildError found in HTML")
        else:
            results.add_pass("Homepage BuildError Check", "No BuildError detected")
        
        # Check for auth.register references (should be removed)
        if "auth.register" in homepage_html:
            results.add_fail("Homepage auth.register Check", "auth.register still referenced")
        else:
            results.add_pass("Homepage auth.register Check", "No auth.register found")
    
    # Test core blueprint routes (these use core_bp prefix)
    test_url(f"{BASE_URL}/about", "About Page", results)
    
    # 2. TEST AUTHENTICATION ROUTES
    print("\n📍 TEST 2: AUTHENTICATION SYSTEM")
    print("-"*70)
    
    login_html = test_url(f"{BASE_URL}/auth/login", "Login Page", results)
    
    if login_html:
        # Check for removed auth.register links
        if "auth.register" in login_html or "auth_bp.register" in login_html:
            results.add_fail("Login auth.register Check", "Register link still present")
        else:
            results.add_pass("Login auth.register Check", "No register links found")
    
    test_url(f"{BASE_URL}/auth/logout", "Logout Route", results, check_redirect=True)
    
    # 3. TEST ALUMNI & NETWORKING
    print("\n📍 TEST 3: ALUMNI & NETWORKING")
    print("-"*70)
    
    test_url(f"{BASE_URL}/alumni", "Alumni Directory", results)
    test_url(f"{BASE_URL}/alumni/directory", "Alumni Directory Page", results)
    test_url(f"{BASE_URL}/mentors", "Mentors Hub", results)
    test_url(f"{BASE_URL}/connections", "Connections", results)
    
    # 4. TEST STORIES SECTION (Fixed stories_bp -> stories)
    print("\n📍 TEST 4: STORIES SECTION")
    print("-"*70)
    
    test_url(f"{BASE_URL}/stories", "Stories List", results)
    test_url(f"{BASE_URL}/stories/manage", "Stories Management", results)
    
    # 5. TEST EVENTS (Fixed events_bp -> events)
    print("\n📍 TEST 5: EVENTS SECTION")
    print("-"*70)
    
    test_url(f"{BASE_URL}/events", "Events Page", results)
    test_url(f"{BASE_URL}/events/upcoming", "Upcoming Events", results)
    
    # 6. TEST COMMUNITY FEATURES
    print("\n📍 TEST 6: COMMUNITY FEATURES")
    print("-"*70)
    
    test_url(f"{BASE_URL}/community", "Community Hub", results)
    test_url(f"{BASE_URL}/feed", "Community Feed", results)
    test_url(f"{BASE_URL}/groups", "Groups", results)
    test_url(f"{BASE_URL}/digests", "Digests", results)
    
    # 7. TEST MESSAGING & NOTIFICATIONS (Fixed _bp suffixes)
    print("\n📍 TEST 7: MESSAGING & NOTIFICATIONS")
    print("-"*70)
    
    test_url(f"{BASE_URL}/messages", "Messages Inbox", results)
    test_url(f"{BASE_URL}/notifications", "Notifications Center", results)
    
    # 8. TEST PROFILE & DASHBOARD
    print("\n📍 TEST 8: PROFILE & DASHBOARD")
    print("-"*70)
    
    test_url(f"{BASE_URL}/profile", "Profile Page", results)
    test_url(f"{BASE_URL}/profile/dashboard", "Profile Dashboard", results)
    
    # 9. TEST CAREERS & SCHOLARSHIPS
    print("\n📍 TEST 9: CAREERS & SCHOLARSHIPS")
    print("-"*70)
    
    test_url(f"{BASE_URL}/careers", "Careers Page", results)
    test_url(f"{BASE_URL}/scholarships", "Scholarships Page", results)
    
    # 10. TEST ANALYTICS
    print("\n📍 TEST 10: ANALYTICS DASHBOARD")
    print("-"*70)
    
    test_url(f"{BASE_URL}/analytics", "Analytics Dashboard", results)
    
    # 11. TEST MENTORSHIP (Fixed mentorship_bp -> mentorship)
    print("\n📍 TEST 11: MENTORSHIP SYSTEM")
    print("-"*70)
    
    test_url(f"{BASE_URL}/mentorship", "Mentorship Dashboard", results)
    
    # 12. TEST DEPARTMENTS & FACULTY
    print("\n📍 TEST 12: DEPARTMENTS & FACULTY")
    print("-"*70)
    
    test_url(f"{BASE_URL}/departments", "Departments Page", results)
    
    # 13. TEST OPPORTUNITIES
    print("\n📍 TEST 13: OPPORTUNITIES")
    print("-"*70)
    
    test_url(f"{BASE_URL}/opportunities", "Opportunities Page", results)
    
    # Print final summary
    success = results.summary()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        sys.exit(1)
