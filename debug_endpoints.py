"""Debug script to check all registered endpoints"""
from app_pro import app

print("\n" + "="*80)
print("CHECKING ALL NAVBAR ENDPOINTS")
print("="*80)

# Test endpoints used in navbar
test_endpoints = [
    'index',
    'scholarships.index',
    'careers.index', 
    'alumni.index',
    'dining.dining_home',
    'housing.index',
    'events.events_home',
    'analytics.index',
    'announcements_bp.index',
    'mentors.index',
    'portfolio.index',
    'profile.profile_home',
]

with app.app_context():
    print("\n✅ Testing navbar endpoints:\n")
    for endpoint in test_endpoints:
        try:
            url = app.url_map.bind('').build(endpoint)
            print(f"  ✅ {endpoint:35} -> {url}")
        except Exception as e:
            print(f"  ❌ {endpoint:35} -> ERROR: {e}")
    
    print("\n" + "="*80)
    print("ALL REGISTERED ENDPOINTS (filtered for navbar-related)")
    print("="*80 + "\n")
    
    # Show all endpoints that might be relevant
    keywords = ['scholar', 'career', 'alumni', 'dining', 'housing', 'event', 'analytic', 'announce', 'mentor', 'portfolio']
    
    for rule in sorted(app.url_map.iter_rules(), key=lambda x: x.endpoint):
        if not rule.rule.startswith('/static'):
            for keyword in keywords:
                if keyword in rule.endpoint.lower() or keyword in rule.rule.lower():
                    print(f"{rule.endpoint:40} -> {rule.rule}")
                    break
