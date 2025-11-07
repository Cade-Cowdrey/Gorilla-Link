"""
Script to add error handling to index routes with database queries
This ensures routes gracefully handle missing tables/database errors
"""

import os
import re

# Routes to fix with their files
ROUTES_TO_FIX = [
    'blueprints/dining/routes.py',
    'blueprints/events/routes.py',
    'blueprints/housing/routes.py',
    'blueprints/scholarships/routes.py',
    'blueprints/mentors/routes.py',
    'blueprints/portfolio/routes.py',
    'blueprints/announcements/routes.py',
]

def add_error_handling_to_route(file_path):
    """Add try/except to index route if it has database queries"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file already has logging import
    has_logging = 'import logging' in content
    has_logger = 'logger = logging.getLogger' in content
    
    # Add logging import if not present
    if not has_logging:
        # Add after the first import block
        first_import_match = re.search(r'(from flask import [^\n]+\n)', content)
        if first_import_match:
            insert_pos = first_import_match.end()
            content = content[:insert_pos] + 'import logging\n' + content[insert_pos:]
    
    if not has_logger:
        # Add logger after imports
        import_section_end = content.find('\nbp = ')
        if import_section_end == -1:
            import_section_end = content.find('\n\n@bp')
        if import_section_end != -1:
            content = content[:import_section_end] + '\n\nlogger = logging.getLogger(__name__)\n' + content[import_section_end:]
    
    # Find the index function
    index_pattern = r'(@bp\.(get|route)\([\'\"]/[\'\"]\)\s*(?:\n@[^\n]+\s*)*\ndef index\([^)]*\):.*?)(\n@bp|\nif __name__|$)'
    
    match = re.search(index_pattern, content, re.DOTALL)
    
    if not match:
        print(f"  ⏭️  No index route found in {file_path}")
        return False
    
    route_code = match.group(1)
    
    # Check if route already has try/except
    if 'try:' in route_code and 'except' in route_code:
        print(f"  ✅ Already has error handling in {file_path}")
        return False
    
    # Check if route has database queries
    if '.query.' not in route_code:
        print(f"  ⏭️  No database queries in {file_path}")
        return False
    
    # Extract function signature and body
    func_match = re.search(r'(def index\([^)]*\):)(.*)', route_code, re.DOTALL)
    if not func_match:
        return False
    
    func_sig = func_match.group(1)
    func_body = func_match.group(2)
    
    # Find the return statement
    return_match = re.search(r'(\s+return render_template\([^)]+\))', func_body, re.DOTALL)
    if not return_match:
        print(f"  ⏭️  No render_template in {file_path}")
        return False
    
    # Get indentation
    lines = func_body.split('\n')
    first_line_with_content = next((line for line in lines if line.strip()), '')
    indent = len(first_line_with_content) - len(first_line_with_content.lstrip())
    indent_str = ' ' * indent
    
    # Build new function body with try/except
    # Find all query assignments
    query_pattern = r'(\s+)(\w+)\s*=\s*([^\n]+\.query[^\n]+)'
    queries = list(re.finditer(query_pattern, func_body))
    
    if not queries:
        return False
    
    # Build new body
    new_body = f"\n{indent_str}try:\n"
    
    # Add all lines before queries with extra indent
    before_queries = func_body[:queries[0].start()].rstrip()
    if before_queries:
        for line in before_queries.split('\n'):
            if line.strip():
                new_body += f"{indent_str}    {line.strip()}\n"
    
    # Add queries with extra indent
    last_end = queries[0].start()
    for query_match in queries:
        # Add any content between last query and this one
        between = func_body[last_end:query_match.start()].strip()
        if between:
            for line in between.split('\n'):
                if line.strip():
                    new_body += f"{indent_str}    {line.strip()}\n"
        
        # Add the query
        var_name = query_match.group(2)
        query_code = query_match.group(3).strip()
        new_body += f"{indent_str}    {var_name} = {query_code}\n"
        last_end = query_match.end()
    
    # Add the rest after queries (including return)
    after_queries = func_body[last_end:].strip()
    for line in after_queries.split('\n'):
        if line.strip():
            new_body += f"{indent_str}    {line.strip()}\n"
    
    # Add except block
    new_body += f"{indent_str}except Exception as e:\n"
    new_body += f"{indent_str}    logger.error(f\"Error in index route: {{e}}\")\n"
    
    # Set empty values for variables
    for query_match in queries:
        var_name = query_match.group(2)
        new_body += f"{indent_str}    {var_name} = []\n"
    
    # Add the return statement again
    return_stmt = return_match.group(1).strip()
    new_body += f"{indent_str}    {return_stmt}\n"
    
    # Replace in content
    new_route = route_code[:func_match.start(2)] + new_body
    new_content = content[:match.start(1)] + new_route + content[match.end(1):]
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✅ Added error handling to {file_path}")
    return True

def main():
    print("Adding error handling to route index functions...\n")
    
    fixed_count = 0
    for route_file in ROUTES_TO_FIX:
        if os.path.exists(route_file):
            print(f"Processing {route_file}...")
            if add_error_handling_to_route(route_file):
                fixed_count += 1
        else:
            print(f"  ❌ File not found: {route_file}")
    
    print(f"\n✅ Added error handling to {fixed_count} routes")

if __name__ == '__main__':
    main()
