"""
Test script to verify all imports work correctly
Run this to check for import errors and circular dependencies
"""

import sys
print("=" * 60)
print("Testing PSU Connect Imports")
print("=" * 60)

# Test 1: Core imports
print("\n1. Testing core imports...")
try:
    from extensions import db, redis_client, cache, limiter
    print("   ✅ Extensions imported successfully")
except Exception as e:
    print(f"   ❌ Extensions import failed: {e}")
    sys.exit(1)

# Test 2: Models
print("\n2. Testing models...")
try:
    from models import (
        User, Role, Scholarship, Job, Resume, ResumeSection, 
        ResumeTemplate, Connection, Notification, Event,
        Company, JobPosting, Application
    )
    print("   ✅ Core models imported successfully")
except Exception as e:
    print(f"   ❌ Core models import failed: {e}")
    sys.exit(1)

# Test 3: Growth Feature Models
print("\n3. Testing growth feature models...")
try:
    from models_growth_features import (
        Badge, UserBadge, UserPoints, AchievementProgress,
        SuccessStory, StoryLike, StoryView,
        Referral, Recommendation, UserBehavior, UserAnalytics,
        ChatMessage, ForumCategory, ForumTopic, ForumPost, ForumVote,
        MentorshipProgram, MentorProfile, MenteeProfile, MentorshipMatch, MentorshipSession,
        AutoApplyQueue, PushSubscription, NotificationPreference,
        DirectMessage, UserMessageCredits,
        LiveEvent, EventAttendee, EventMessage
    )
    print("   ✅ Growth feature models imported successfully")
except Exception as e:
    print(f"   ❌ Growth feature models import failed: {e}")
    sys.exit(1)

# Test 4: Core Blueprints
print("\n4. Testing core blueprints...")
try:
    from blueprints.core.routes import bp as core_bp
    print("   ✅ Core blueprint imported")
except Exception as e:
    print(f"   ⚠️  Core blueprint: {e}")

try:
    from blueprints.auth.routes import bp as auth_bp
    print("   ✅ Auth blueprint imported")
except Exception as e:
    print(f"   ⚠️  Auth blueprint: {e}")

# Test 5: Growth Feature Blueprints
print("\n5. Testing growth feature blueprints...")
blueprints_to_test = [
    ('gamification', 'gamification_bp'),
    ('success_stories', 'success_stories_bp'),
    ('referrals', 'referrals_bp'),
    ('recommendations', 'recommendations_bp'),
    ('ai_coach', 'ai_coach_bp'),
    ('forums', 'forums_bp'),
    ('mentorship', 'mentorship_bp'),
    ('auto_apply', 'auto_apply_bp'),
    ('push_notifications', 'push_notifications_bp'),
    ('messages', 'messages_bp'),
]

failed_imports = []
for module_name, bp_name in blueprints_to_test:
    try:
        module = __import__(f'blueprints.{module_name}', fromlist=[bp_name])
        if hasattr(module, bp_name):
            print(f"   ✅ {module_name} blueprint imported")
        else:
            print(f"   ⚠️  {module_name}: No '{bp_name}' attribute")
            failed_imports.append(module_name)
    except Exception as e:
        print(f"   ❌ {module_name}: {e}")
        failed_imports.append(module_name)

# Test 6: Analytics & Events
print("\n6. Testing analytics and events...")
try:
    from blueprints.analytics.user_dashboard import analytics_bp
    print("   ✅ Analytics blueprint imported")
except Exception as e:
    print(f"   ❌ Analytics: {e}")

try:
    from blueprints.events.live import events_bp
    print("   ✅ Events blueprint imported")
except Exception as e:
    print(f"   ❌ Events: {e}")

try:
    from blueprints.admin.dashboard import admin_growth_bp
    print("   ✅ Admin dashboard imported")
except Exception as e:
    print(f"   ❌ Admin dashboard: {e}")

# Summary
print("\n" + "=" * 60)
if failed_imports:
    print(f"⚠️  {len(failed_imports)} blueprint(s) had issues: {', '.join(failed_imports)}")
else:
    print("✅ All imports successful!")
print("=" * 60)
