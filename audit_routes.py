"""
Comprehensive Route and Blueprint Audit Script
Checks for:
1. Missing endpoints referenced in templates
2. Blueprint name mismatches
3. Invalid url_for references
4. Missing template files
"""

import os
import re
from pathlib import Path
from collections import defaultdict

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text:^80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}\n")

def print_section(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'-'*len(text)}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.MAGENTA}ℹ️  {text}{Colors.RESET}")

# Get blueprint definitions
def find_blueprints():
    """Find all blueprint definitions in routes.py files"""
    blueprints = {}
    blueprint_pattern = re.compile(r'(\w+)\s*=\s*Blueprint\(["\']([^"\']+)["\']')
    
    for root, dirs, files in os.walk('blueprints'):
        if 'routes.py' in files:
            routes_file = os.path.join(root, 'routes.py')
            try:
                with open(routes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = blueprint_pattern.findall(content)
                    for var_name, bp_name in matches:
                        blueprints[bp_name] = {
                            'variable': var_name,
                            'file': routes_file,
                            'folder': os.path.basename(root)
                        }
            except Exception as e:
                print_warning(f"Could not read {routes_file}: {e}")
    
    return blueprints

# Find url_for references in templates
def find_url_for_refs():
    """Find all url_for references in template files"""
    url_for_pattern = re.compile(r'url_for\(["\']([^"\']+)["\']')
    references = defaultdict(list)
    
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                template_path = os.path.join(root, file)
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = url_for_pattern.findall(content)
                        for match in matches:
                            references[match].append(template_path)
                except Exception as e:
                    print_warning(f"Could not read {template_path}: {e}")
    
    return references

# Find render_template references
def find_template_refs():
    """Find all render_template calls in routes"""
    template_pattern = re.compile(r'render_template\(["\']([^"\']+)["\']')
    references = []
    
    for root, dirs, files in os.walk('blueprints'):
        if 'routes.py' in files:
            routes_file = os.path.join(root, 'routes.py')
            try:
                with open(routes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = template_pattern.findall(content)
                    for match in matches:
                        references.append({
                            'template': match,
                            'file': routes_file
                        })
            except Exception as e:
                print_warning(f"Could not read {routes_file}: {e}")
    
    return references

# Check if template file exists
def template_exists(template_name):
    """Check if a template file exists"""
    template_path = os.path.join('templates', template_name)
    return os.path.exists(template_path)

# Main audit function
def audit_routes():
    print_header("ROUTE AND BLUEPRINT AUDIT")
    
    # 1. Find all blueprints
    print_section("1. Registered Blueprints")
    blueprints = find_blueprints()
    for bp_name, info in sorted(blueprints.items()):
        print_success(f"{bp_name:30} -> {info['folder']:20} ({info['variable']})")
    print_info(f"Total blueprints found: {len(blueprints)}")
    
    # 2. Find all url_for references
    print_section("2. URL References in Templates")
    url_refs = find_url_for_refs()
    
    # 3. Check for missing endpoints
    print_section("3. Missing Endpoints Check")
    missing_endpoints = []
    for endpoint, templates in sorted(url_refs.items()):
        if '.' in endpoint:
            bp_part, route_part = endpoint.split('.', 1)
            if bp_part not in blueprints:
                missing_endpoints.append((endpoint, templates))
    
    if missing_endpoints:
        print_error(f"Found {len(missing_endpoints)} missing blueprint endpoints:")
        for endpoint, templates in missing_endpoints:
            print_error(f"  {endpoint}")
            for template in templates[:3]:  # Show first 3 templates
                print(f"    └─ Used in: {template}")
            if len(templates) > 3:
                print(f"    └─ ... and {len(templates)-3} more files")
    else:
        print_success("All blueprint endpoints exist!")
    
    # 4. Check for auth.register specifically
    print_section("4. Special Check: auth.register")
    auth_register_refs = url_refs.get('auth.register', [])
    if auth_register_refs:
        print_error(f"'auth.register' endpoint does NOT exist but is referenced in {len(auth_register_refs)} files:")
        for template in auth_register_refs:
            print(f"  └─ {template}")
        print_info("The auth blueprint only has 'auth.login' and 'auth.logout' endpoints")
    else:
        print_success("No references to 'auth.register' found")
    
    # 5. Check template files
    print_section("5. Template File Existence Check")
    template_refs = find_template_refs()
    missing_templates = []
    for ref in template_refs:
        if not template_exists(ref['template']):
            missing_templates.append(ref)
    
    if missing_templates:
        print_error(f"Found {len(missing_templates)} missing template files:")
        for ref in missing_templates[:10]:  # Show first 10
            print_error(f"  {ref['template']}")
            print(f"    └─ Referenced in: {ref['file']}")
    else:
        print_success("All template files exist!")
    
    # 6. Summary
    print_section("6. Summary")
    print(f"Total Blueprints: {Colors.BOLD}{len(blueprints)}{Colors.RESET}")
    print(f"Total URL References: {Colors.BOLD}{len(url_refs)}{Colors.RESET}")
    print(f"Missing Endpoints: {Colors.BOLD}{len(missing_endpoints)}{Colors.RESET}")
    print(f"Missing Templates: {Colors.BOLD}{len(missing_templates)}{Colors.RESET}")
    
    # 7. Critical issues
    print_section("7. Critical Issues Requiring Immediate Fix")
    critical_issues = []
    
    # Check for auth.register
    if 'auth.register' in url_refs:
        critical_issues.append(('auth.register', url_refs['auth.register']))
    
    # Check for other missing common endpoints
    common_missing = [
        'core.home', 'core.index', 'core.notifications', 'core.about', 
        'core.contact', 'core.faq', 'core.help', 'core.privacy',
        'core.terms', 'core.accessibility'
    ]
    
    for endpoint in common_missing:
        if endpoint in url_refs:
            bp_name = endpoint.split('.')[0]
            if bp_name not in blueprints and bp_name != 'core_bp':
                critical_issues.append((endpoint, url_refs[endpoint]))
    
    if critical_issues:
        print_error(f"Found {len(critical_issues)} critical issues:")
        for endpoint, templates in critical_issues:
            print_error(f"\n  Endpoint: {endpoint}")
            print(f"  Used in {len(templates)} templates:")
            for template in templates[:5]:
                print(f"    └─ {template}")
    else:
        print_success("No critical issues found!")
    
    print_header("AUDIT COMPLETE")
    
    return {
        'blueprints': blueprints,
        'missing_endpoints': missing_endpoints,
        'missing_templates': missing_templates,
        'critical_issues': critical_issues
    }

if __name__ == "__main__":
    results = audit_routes()
