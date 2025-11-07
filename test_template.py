"""Test base.html template rendering"""
from app_pro import app
from flask import render_template_string

print("\n" + "="*70)
print("TESTING BASE.HTML TEMPLATE RENDERING")
print("="*70)

with app.app_context():
    try:
        # Try to render a simple template that extends base.html
        test_template = """
        {% extends "base.html" %}
        {% block title %}Test Page{% endblock %}
        {% block content %}
        <h1>Test Content</h1>
        {% endblock %}
        """
        
        result = render_template_string(test_template)
        print("\n✅ SUCCESS: base.html template renders without errors!")
        print(f"   Generated {len(result)} characters of HTML")
        
        # Check if navbar links are present
        if 'href="/scholarships/"' in result:
            print("✅ Scholarships link found")
        if 'href="/careers/"' in result:
            print("✅ Careers link found")
        if 'href="/analytics/"' in result:
            print("✅ Analytics link found")
        if 'href="/announcements/"' in result:
            print("✅ Announcements link found")
            
    except Exception as e:
        print(f"\n❌ ERROR rendering base.html:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("="*70)
