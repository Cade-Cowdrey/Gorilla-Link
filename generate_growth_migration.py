"""
Generate Database Migration for Growth Features
Creates Alembic migration for all 31 new models
"""

import os
import sys

def generate_migration():
    """Generate migration for growth features models"""
    
    print("\n" + "="*60)
    print("PSU CONNECT - GENERATING GROWTH FEATURES MIGRATION")
    print("="*60 + "\n")
    
    print("This will create a migration for 31 new models:")
    print("  • Badge, UserBadge, UserStreak")
    print("  • ProfileCompletionProgress")
    print("  • UserPoints, PointTransaction")
    print("  • SuccessStory, StoryReaction, StoryComment")
    print("  • Referral")
    print("  • DirectMessage, UserMessageCredits")
    print("  • ForumCategory, ForumTopic, ForumPost, ForumVote")
    print("  • MentorshipProgram, MentorProfile, MenteeProfile")
    print("  • MentorshipMatch, MentorshipSession")
    print("  • UserAnalytics")
    print("  • Recommendation, UserBehavior")
    print("  • AutoApplyQueue")
    print("  • NotificationPreference, PushSubscription")
    print("  • ChatMessage")
    print()
    
    # Check if models file exists
    if not os.path.exists('models_growth_features.py'):
        print("❌ Error: models_growth_features.py not found!")
        return False
    
    print("Step 1: Ensure models are imported in app...")
    print("  Add to app_pro.py or app.py:")
    print("  from models_growth_features import *")
    print()
    
    print("Step 2: Run Flask-Migrate commands...")
    print()
    
    commands = [
        {
            'cmd': 'flask db migrate -m "Add growth features models"',
            'desc': 'Generate migration file'
        },
        {
            'cmd': 'flask db upgrade',
            'desc': 'Apply migration to database'
        },
        {
            'cmd': 'python seed_growth_features.py',
            'desc': 'Seed initial data'
        }
    ]
    
    for cmd_info in commands:
        print(f"Run: {cmd_info['cmd']}")
        print(f"     ({cmd_info['desc']})")
        print()
    
    print("="*60)
    print("MANUAL STEPS REQUIRED:")
    print("="*60)
    print()
    print("1. Add import to your main app file:")
    print("   from models_growth_features import *")
    print()
    print("2. Run the commands above in order")
    print()
    print("3. Verify migration file in migrations/versions/")
    print()
    print("4. Test the migration on a development database first")
    print()
    
    # Create a helper script
    script_content = """#!/bin/bash
# PSU Connect - Apply Growth Features Migration

echo "Applying Growth Features Migration..."
echo ""

# Step 1: Generate migration
echo "Step 1: Generating migration..."
flask db migrate -m "Add growth features models"
echo ""

# Step 2: Review migration
echo "Step 2: Review the migration file in migrations/versions/"
echo "Press Enter when ready to continue..."
read

# Step 3: Apply migration
echo "Step 3: Applying migration to database..."
flask db upgrade
echo ""

# Step 4: Seed data
echo "Step 4: Seeding initial data..."
python seed_growth_features.py
echo ""

echo "✓ Migration complete!"
"""
    
    with open('apply_growth_migration.sh', 'w') as f:
        f.write(script_content)
    
    print("✓ Created helper script: apply_growth_migration.sh")
    print("  Run: bash apply_growth_migration.sh")
    print()
    
    # Create PowerShell version for Windows
    ps_script = """# PSU Connect - Apply Growth Features Migration

Write-Host "Applying Growth Features Migration..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate migration
Write-Host "Step 1: Generating migration..." -ForegroundColor Yellow
flask db migrate -m "Add growth features models"
Write-Host ""

# Step 2: Review migration
Write-Host "Step 2: Review the migration file in migrations/versions/" -ForegroundColor Yellow
Write-Host "Press Enter when ready to continue..."
Read-Host

# Step 3: Apply migration
Write-Host "Step 3: Applying migration to database..." -ForegroundColor Yellow
flask db upgrade
Write-Host ""

# Step 4: Seed data
Write-Host "Step 4: Seeding initial data..." -ForegroundColor Yellow
python seed_growth_features.py
Write-Host ""

Write-Host "✓ Migration complete!" -ForegroundColor Green
"""
    
    with open('apply_growth_migration.ps1', 'w') as f:
        f.write(ps_script)
    
    print("✓ Created PowerShell script: apply_growth_migration.ps1")
    print("  Run: .\\apply_growth_migration.ps1")
    print()
    
    return True


if __name__ == '__main__':
    generate_migration()
