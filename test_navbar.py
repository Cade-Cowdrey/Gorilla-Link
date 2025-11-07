"""Simple endpoint test"""
from app_pro import app

test_endpoints = [
    'index',
    'scholarships.index',
    'careers.index', 
    'alumni.index',
    'dining.dining_home',
    'housing.index',
    'events.events_home',
    'analytics_bp.index',
    'announcements_bp.index',
    'mentors.index',
    'portfolio.index',
    'profile.profile_home',
]

with app.app_context():
    print("\nTesting navbar endpoints:")
    print("=" * 60)
    
    all_pass = True
    for endpoint in test_endpoints:
        try:
            url = app.url_map.bind('').build(endpoint)
            print(f"OK   {endpoint:35} -> {url}")
        except Exception as e:
            print(f"FAIL {endpoint:35} -> {str(e)[:50]}")
            all_pass = False
    
    print("=" * 60)
    if all_pass:
        print("ALL NAVBAR ENDPOINTS WORKING!")
    else:
        print("SOME ENDPOINTS FAILED!")
