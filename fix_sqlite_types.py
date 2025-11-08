"""
Fix PostgreSQL-specific types (ARRAY, JSONB) to work with SQLite
"""
import os
import re

# Files to fix
model_files = [
    'models.py',
    'models_extended.py',
    'models_growth_features.py',
    'models_dining.py',
    'models_portfolio.py',
    'models_advanced_features.py',
    'models_student_features.py',
    'models_innovative_features.py'
]

# Check which files exist
existing_files = [f for f in model_files if os.path.exists(f)]

print(f"Found {len(existing_files)} model files to fix")

for filename in existing_files:
    print(f"\nProcessing {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add USE_POSTGRES check if not already present
    if 'USE_POSTGRES' not in content:
        # Add after imports
        import_section = content.split('\n\n')[0]
        rest_of_file = '\n\n'.join(content.split('\n\n')[1:])
        
        content = import_section + '\n\n'
        content += '# Determine if we\'re using PostgreSQL or SQLite\n'
        content += 'import os\n'
        content += 'DATABASE_URL = os.getenv(\'DATABASE_URL\', \'sqlite:///pittstate_connect_local.db\')\n'
        content += 'USE_POSTGRES = DATABASE_URL.startswith(\'postgresql\')\n\n'
        content += rest_of_file
    
    # Replace JSONB with conditional
    content = re.sub(
        r'db\.Column\(JSONB\)',
        r'db.Column(JSONB if USE_POSTGRES else JSON)',
        content
    )
    
    content = re.sub(
        r'db\.Column\(JSONB,',
        r'db.Column(JSONB if USE_POSTGRES else JSON,',
        content
    )
    
    # Replace ARRAY with conditional
    content = re.sub(
        r'db\.Column\(ARRAY\(([^)]+)\)\)',
        r'db.Column(ARRAY(\1) if USE_POSTGRES else JSON)',
        content
    )
    
    content = re.sub(
        r'db\.Column\(ARRAY\(([^)]+)\),',
        r'db.Column(ARRAY(\1) if USE_POSTGRES else JSON,',
        content
    )
    
    if content != original_content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed {filename}")
    else:
        print(f"⏭️  No changes needed for {filename}")

print("\n✅ All model files have been fixed for SQLite compatibility!")
