#!/usr/bin/env python3
"""
Script to add __table_args__ = {'extend_existing': True} to all model classes
"""
import re

def fix_models():
    with open('models_growth_features.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all classes that don't have __table_args__ with extend_existing
    lines = content.split('\n')
    modified = []
    i = 0
    changes = 0
    
    while i < len(lines):
        line = lines[i]
        # Check if this is a class definition
        if re.match(r'^class \w+\(db\.Model\):', line):
            # Check next few lines for __table_args__
            has_table_args = False
            for j in range(i+1, min(i+5, len(lines))):
                if '__table_args__' in lines[j]:
                    has_table_args = True
                    break
            
            modified.append(line)
            # If no table_args and next line is __tablename__, add after it
            if not has_table_args and i+1 < len(lines) and '__tablename__' in lines[i+1]:
                i += 1
                modified.append(lines[i])  # Add __tablename__ line
                modified.append("    __table_args__ = {'extend_existing': True}")
                changes += 1
                i += 1
                continue
        
        modified.append(line)
        i += 1
    
    with open('models_growth_features.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(modified))
    
    print(f'✅ Added extend_existing to {changes} model classes')

if __name__ == '__main__':
    fix_models()
