from app_pro import app

with app.app_context():
    rules = [str(rule) for rule in app.url_map.iter_rules() if not rule.rule.startswith('/static')]
    
    # Check for specific blueprints
    blueprints_to_check = [
        'textbook', 'student_discounts', 'wait_times', 
        'course_library', 'professor', 'grade_explorer',
        'housing', 'dining', 'events', 'scholarships',
        'careers', 'alumni', 'gpa_calculator', 'mentors',
        'portfolio', 'analytics_bp', 'announcements_bp'
    ]
    
    print("=== Checking Blueprint Routes ===\n")
    for blueprint in blueprints_to_check:
        matching = [r for r in rules if blueprint in r]
        if matching:
            print(f"✅ {blueprint}: {len(matching)} routes")
            for route in matching[:3]:
                print(f"   - {route}")
        else:
            print(f"❌ {blueprint}: NO ROUTES FOUND")
    
    print("\n=== All Non-Static Routes (first 100) ===")
    for rule in sorted(rules)[:100]:
        print(rule)
