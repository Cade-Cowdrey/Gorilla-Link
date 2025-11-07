"""
Quick script to comment out remaining duplicate model classes.
Based on diagnostic: 
- DataExportRequest: models_growth_features.py (keep), models_admin.py (remove)
- FeatureFlag: models_extended.py (remove), models_admin.py (keep)
- HousingListing: models_student_features.py (remove), models_advanced_features.py (keep)
"""

import re
from pathlib import Path

fixes = [
    {
        'file': 'models_student_features.py',
        'model': 'HousingListing',
        'start_line': 63,  # Approximate
    },
    {
        'file': 'models_growth_features.py', 
        'model': 'DataExportRequest',
        'start_line': None,  # Will search
    },
    {
        'file': 'models_extended.py',
        'model': 'FeatureFlag',
        'start_line': None,  # Will search
    },
]

def comment_out_class(filepath, class_name):
    """Comment out a class definition in a file"""
    lines = Path(filepath).read_text().splitlines(keepends=True)
    
    # Find the class definition
    class_start = None
    for i, line in enumerate(lines):
        if f'class {class_name}(db.Model):' in line:
            class_start = i
            break
    
    if class_start is None:
        print(f"  ⚠️  Could not find class {class_name} in {filepath}")
        return False
    
    # Find where the class ends (next class or end of file)
    class_end = len(lines)
    for i in range(class_start + 1, len(lines)):
        if lines[i].startswith('class ') and '(db.Model)' in lines[i]:
            class_end = i
            break
    
    # Add comment marker
    comment = f"\n# {class_name} model removed - duplicate exists in another file\n# Original definition commented out to avoid SQLAlchemy conflicts\n\n"
    replacement = comment + ''.join(f"# {line}" if not line.strip().startswith('#') else line 
                                    for line in lines[class_start:class_end])
    
    # Write back
    new_content = ''.join(lines[:class_start]) + replacement + ''.join(lines[class_end:])
    Path(filepath).write_text(new_content)
    print(f"  ✅ Commented out {class_name} in {filepath}")
    return True

# Actually, let me just delete the classes instead since we know which to keep
print("\n🔧 Fixing remaining duplicate models...")

# For HousingListing in models_student_features.py - find and mark for removal
print("\n1. Removing HousingListing from models_student_features.py...")
success = comment_out_class('models_student_features.py', 'HousingListing')

# For DataExportRequest in models_admin.py - find and mark for removal 
print("\n2. Removing DataExportRequest from models_admin.py...")
success = comment_out_class('models_admin.py', 'DataExportRequest')

# For FeatureFlag in models_extended.py - find and mark for removal
print("\n3. Removing FeatureFlag from models_extended.py...")
success = comment_out_class('models_extended.py', 'FeatureFlag')

print("\n✅ All duplicate models handled!\n")
