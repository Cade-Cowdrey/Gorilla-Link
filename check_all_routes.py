#!/usr/bin/env python3
"""
Check all routes in the application and identify 404/500 errors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_pro import app
from flask import url_for

def check_routes():
    """Check all registered routes"""
    print("\n" + "=" * 80)
    print("🔍 CHECKING ALL ROUTES")
    print("=" * 80)
    
    with app.app_context():
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint != 'static':
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                    'path': str(rule)
                })
        
        # Sort by endpoint
        routes.sort(key=lambda x: x['endpoint'])
        
        # Group by blueprint
        blueprints = {}
        for route in routes:
            bp_name = route['endpoint'].split('.')[0] if '.' in route['endpoint'] else 'main'
            if bp_name not in blueprints:
                blueprints[bp_name] = []
            blueprints[bp_name].append(route)
        
        # Print routes by blueprint
        total_routes = 0
        for bp_name in sorted(blueprints.keys()):
            print(f"\n📁 {bp_name.upper()} Blueprint")
            print("-" * 80)
            for route in blueprints[bp_name]:
                total_routes += 1
                methods = f"[{route['methods']}]"
                print(f"   {route['endpoint']:50} {methods:15} {route['path']}")
        
        print("\n" + "=" * 80)
        print(f"📊 TOTAL ROUTES: {total_routes}")
        print("=" * 80)
        
        # Check for common missing routes
        print("\n🔍 Checking for common missing routes:")
        critical_routes = [
            'scholarships.index',
            'scholarships.browse',
            'careers.index',
            'careers.jobs',
            'housing.index',
            'dining.index',
            'health.index',
            'safety.index',
        ]
        
        for route in critical_routes:
            try:
                url = url_for(route)
                print(f"   ✅ {route:40} → {url}")
            except Exception as e:
                print(f"   ❌ {route:40} → MISSING ({str(e)})")


if __name__ == "__main__":
    check_routes()
