# generate_blueprints.py
"""Scaffold consistent blueprints using *_bp naming. Does not modify app_pro.py."""
from pathlib import Path


EXPECTED = [
'core', 'auth', 'analytics', 'api', 'campus', 'connections', 'marketing', 'map',
'mentorship', 'opportunities', 'portfolio', 'stories', 'students', 'admin', 'alumni',
'careers', 'digests'
]


ROOT = Path(__file__).resolve().parent
BP_DIR = ROOT / 'blueprints'
TPL_DIR = ROOT / 'templates'


BLUEPRINT_TEMPLATE = """from flask import Blueprint, render_template


{bp_name}_bp = Blueprint('{bp_name}', __name__, url_prefix='/{bp_name}')


@{bp_name}_bp.get('/')
def {bp_name}_index():
return render_template('{bp_name}/index.html')
"""


INDEX_TEMPLATE = """{% extends 'base.html' %}
{% block title %}{Title} — PittState-Connect{% endblock %}
{% block content %}
<div class=\"container mx-auto py-8\">
<h1 class=\"text-3xl font-bold mb-4\">{Title}</h1>
<p>Welcome to the {Title} module.</p>
</div>
{% endblock %}
"""




def ensure_bp(name: str):
pkg = BP_DIR / name
pkg.mkdir(parents=True, exist_ok=True)
(pkg / '__init__.py').write_text(f"# package: {name}\n")
routes = pkg / 'routes.py'
if not routes.exists():
routes.write_text(BLUEPRINT_TEMPLATE.format(bp_name=name))


tdir = TPL_DIR / name
tdir.mkdir(parents=True, exist_ok=True)
idx = tdir / 'index.html'
if not idx.exists():
idx.write_text(INDEX_TEMPLATE.format(Title=name.capitalize()))




def main():
for name in EXPECTED:
ensure_bp(name)


if __name__ == '__main__':
main()
